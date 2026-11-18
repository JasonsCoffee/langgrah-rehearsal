// Install only in the authorized game's existing Editor/test assembly.
// Requires its existing Unity Operator, Newtonsoft.Json and TestRunner references.
// Does not start/quit an editor, install packages, or modify shared source.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using jj.UnityOperator.Editor;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.Compilation;
using UnityEditor.TestTools.TestRunner.Api;
using UnityEngine;

namespace UnityCoder
{
    public sealed class FrameworkVerifyCapabilitiesCommand : IUnityOpCommand
    {
        public string CommandName => "FrameworkVerifyCapabilities";
        public string Execute(string json)
        {
            return CommandResult.SuccessWithData(new JObject {
                ["protocol"] = 1, ["command"] = "FrameworkVerify",
                ["modes"] = new JArray("compile", "tests"),
                ["ready"] = !EditorApplication.isCompiling && !EditorApplication.isUpdating,
                ["active_ticket"] = SessionState.GetString("UnityCoder.ActiveVerification", "")
            }.ToString(Newtonsoft.Json.Formatting.None)).ToJson();
        }
    }

    public sealed class FrameworkVerifyCommand : IUnityOpCommand
    {
        public string CommandName => "FrameworkVerify";
        public bool IsLongRunning => true;
        public string Execute(string json)
        {
            try
            {
                UnityCoderVerifier.Begin((string)JObject.Parse(json)["ticket"]);
                return CommandResult.Success().ToJson();
            }
            catch (Exception error) { return CommandResult.Error(error.Message).ToJson(); }
        }
    }

    [InitializeOnLoad]
    public static class UnityCoderVerifier
    {
        private const string ActiveKey = "UnityCoder.ActiveVerification";
        private static TestRunnerApi api;
        private static readonly Callbacks callbacks = new Callbacks();
        private static readonly List<JObject> compilerErrors = new List<JObject>();
        private static bool compilationStarted;

        static UnityCoderVerifier()
        {
            CompilationPipeline.compilationStarted += OnCompilationStarted;
            CompilationPipeline.assemblyCompilationFinished += OnAssemblyFinished;
            CompilationPipeline.compilationFinished += OnCompilationFinished;
            EditorApplication.delayCall += RestoreCallbacks;
        }

        private static string Active => SessionState.GetString(ActiveKey, "");

        private static string DirectoryFor(string ticket)
        {
            if (ticket == null || !Regex.IsMatch(ticket, "^[a-f0-9]{64}$"))
                throw new InvalidOperationException("Invalid verification ticket");
            string root = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            string current = root;
            foreach (string part in new[] { ".agent", "verification", ticket })
            {
                current = Path.Combine(current, part);
                if (Directory.Exists(current) && (File.GetAttributes(current) & FileAttributes.ReparsePoint) != 0)
                    throw new InvalidOperationException("Verification output contains an alias");
            }
            return current;
        }

        private static JObject Envelope(string ticket)
        {
            return JObject.Parse(File.ReadAllText(Path.Combine(DirectoryFor(ticket), "request.json")));
        }

        private static void Write(string ticket, JObject result)
        {
            string folder = DirectoryFor(ticket);
            string target = Path.Combine(folder, "result.json");
            // Completion is immutable. A duplicate callback cannot overwrite proof.
            if (File.Exists(target)) return;
            string temporary = Path.Combine(folder, Guid.NewGuid().ToString("N") + ".tmp");
            try
            {
                File.WriteAllText(temporary, result.ToString(Newtonsoft.Json.Formatting.None));
                File.Move(temporary, target);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
            if (Active == ticket) SessionState.EraseString(ActiveKey);
        }

        private static JObject Result(string ticket)
        {
            JObject envelope = Envelope(ticket);
            return new JObject { ["request"] = envelope["request"].DeepClone(),
                ["mode"] = envelope["mode"], ["status"] = "completed" };
        }

        private static void Operational(string ticket, string message)
        {
            JObject result = Result(ticket);
            result["status"] = "operational";
            result["message"] = message;
            Write(ticket, result);
        }

        private static void RestoreCallbacks()
        {
            if (api == null)
            {
                api = ScriptableObject.CreateInstance<TestRunnerApi>();
                api.RegisterCallbacks(callbacks);
            }
            string ticket = Active;
            if (string.IsNullOrEmpty(ticket)) return;
            if (File.Exists(Path.Combine(DirectoryFor(ticket), "result.json")))
                SessionState.EraseString(ActiveKey);
            else if ((string)Envelope(ticket)["mode"] == "compile")
                Operational(ticket, "Reload interrupted compilation evidence; reconcile before another request");
            // For tests, restore callbacks without re-executing the test run.
        }

        public static void Begin(string ticket)
        {
            JObject envelope = Envelope(ticket);
            if (File.Exists(Path.Combine(DirectoryFor(ticket), "result.json"))) return;
            if (!string.IsNullOrEmpty(Active))
            {
                if (Active == ticket) return;
                throw new InvalidOperationException("Another verification request owns the editor");
            }
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                Operational(ticket, "Editor is not idle; reconcile and retry with a new request after readiness");
                return;
            }
            string mode = (string)envelope["mode"];
            if (mode != "compile" && mode != "tests") throw new InvalidOperationException("Unsupported gate");
            if (envelope["request"] == null || string.IsNullOrEmpty((string)envelope["request"]["candidate_revision"]))
                throw new InvalidOperationException("Missing candidate provenance");
            RestoreCallbacks();
            SessionState.SetString(ActiveKey, ticket);
            try
            {
                if (mode == "compile")
                {
                    compilerErrors.Clear();
                    compilationStarted = false;
                    AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                    CompilationPipeline.RequestScriptCompilation();
                }
                else
                {
                    string[] selected = envelope["request"]["test_selection"].ToObject<string[]>();
                    if (selected == null || selected.Length == 0 || selected.Distinct().Count() != selected.Length)
                        throw new InvalidOperationException("Empty or duplicate test selection");
                    api.RetrieveTestList(TestMode.EditMode, tree =>
                    {
                        try
                        {
                            var discovered = new List<string>();
                            Discover(tree, discovered);
                            if (selected.Any(name => !discovered.Contains(name)))
                            {
                                Operational(ticket, "Requested test was not discovered");
                                return;
                            }
                            File.WriteAllText(Path.Combine(DirectoryFor(ticket), "discovered.json"), new JArray(discovered).ToString());
                            api.Execute(new ExecutionSettings(new Filter { testMode = TestMode.EditMode, testNames = selected }));
                        }
                        catch (Exception error) { Operational(ticket, error.Message); }
                    });
                }
            }
            catch (Exception error) { Operational(ticket, error.Message); }
        }

        private static void Discover(ITestAdaptor node, List<string> names)
        {
            if (!node.IsSuite) names.Add(node.FullName);
            foreach (ITestAdaptor child in node.Children) Discover(child, names);
        }

        private static void OnCompilationStarted(object context)
        {
            if (!string.IsNullOrEmpty(Active) && (string)Envelope(Active)["mode"] == "compile")
                compilationStarted = true;
        }

        private static void OnAssemblyFinished(string assembly, CompilerMessage[] messages)
        {
            if (!compilationStarted) return;
            foreach (CompilerMessage message in messages.Where(m => m.type == CompilerMessageType.Error))
            {
                string file = message.file.Replace('\\', '/');
                string root = Path.GetFullPath(Path.Combine(Application.dataPath, "..")).Replace('\\', '/') + "/";
                if (file.StartsWith(root, StringComparison.OrdinalIgnoreCase)) file = file.Substring(root.Length);
                if (Path.IsPathRooted(file)) file = "";
                compilerErrors.Add(new JObject { ["code"] = "compile", ["file"] = file,
                    ["symbol"] = "", ["message"] = message.message });
            }
        }

        private static void OnCompilationFinished(object context)
        {
            string ticket = Active;
            if (string.IsNullOrEmpty(ticket) || !compilationStarted) return;
            JObject result = Result(ticket);
            result["passed"] = compilerErrors.Count == 0;
            result["violations"] = new JArray(compilerErrors);
            Write(ticket, result);
            compilationStarted = false;
        }

        private sealed class Callbacks : ICallbacks
        {
            public void RunStarted(ITestAdaptor tests) { }
            public void TestStarted(ITestAdaptor test) { }
            public void TestFinished(ITestResultAdaptor result) { }
            public void RunFinished(ITestResultAdaptor result)
            {
                string ticket = Active;
                if (string.IsNullOrEmpty(ticket) || (string)Envelope(ticket)["mode"] != "tests") return;
                JObject output = Result(ticket);
                output["discovered"] = JArray.Parse(File.ReadAllText(Path.Combine(DirectoryFor(ticket), "discovered.json")));
                foreach (string group in new[] { "executed", "passed", "failed", "skipped", "inconclusive" })
                    output[group] = new JArray();
                output["failure_details"] = new JArray();
                output["suite_errors"] = new JArray();
                Collect(result, output);
                Write(ticket, output);
            }

            private static void Collect(ITestResultAdaptor node, JObject output)
            {
                string site = node.ToXml().Attributes["site"] ?? "Test";
                // Unity's RecordPrefixedException replaces the failure site for
                // assertion exceptions in setup/teardown. Its message retains
                // the runner prefix; conservatively keep these nonbehavioral.
                if (site == "Test" && !string.IsNullOrEmpty(node.Message))
                    foreach (string line in node.Message.Split('\n'))
                        foreach (string phase in new[] { "SetUp", "TearDown", "OneTimeSetUp", "OneTimeTearDown", "UnitySetUp", "UnityTearDown" })
                            if (line.TrimStart().StartsWith(phase + " :", StringComparison.Ordinal)) site = phase;
                if (node.Test.IsSuite && node.TestStatus.ToString() == "Failed" && site != "Child")
                    ((JArray)output["suite_errors"]).Add(node.FullName + ": " + node.ResultState + ": " + node.Message);
                if (!node.Test.IsSuite)
                {
                    string group = node.TestStatus.ToString().ToLowerInvariant();
                    if (group != "passed" && group != "failed" && group != "skipped") group = "inconclusive";
                    ((JArray)output[group]).Add(node.FullName);
                    if (group == "failed")
                        ((JArray)output["failure_details"]).Add(new JObject {
                            ["test"] = node.FullName, ["state"] = node.ResultState,
                            ["site"] = site, ["message"] = string.IsNullOrEmpty(node.Message) ? node.ResultState : node.Message });
                    if (group == "passed" || group == "failed") ((JArray)output["executed"]).Add(node.FullName);
                }
                foreach (ITestResultAdaptor child in node.Children) Collect(child, output);
            }
        }
    }
}
