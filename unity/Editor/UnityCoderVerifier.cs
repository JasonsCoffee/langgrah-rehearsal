// UnityCoderVerifier.cs
//
// Drop this file into <YourUnityProject>/Assets/Editor/.
// It is invoked by the LangGraph pipeline through:
//
//   Unity.exe -batchmode -nographics -quit \
//     -projectPath <project> \
//     -executeMethod UnityCoder.UnityCoderVerifier.Verify \
//     -unityCoderResult <project>/Temp/unity_coder_result.json \
//     -logFile <project>/Temp/unity_coder_verify.log
//
// Requires com.unity.test-framework (present in any project with EditMode tests).
// If the project fails to compile, -executeMethod never runs and the Python side
// falls back to scraping "error CS" lines from the log file.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.TestTools.TestRunner.Api;
using UnityEngine;

namespace UnityCoder
{
    public static class UnityCoderVerifier
    {
        public static void Verify()
        {
            string resultPath = GetArg("-unityCoderResult");
            string platform = GetArg("-unityCoderPlatform") ?? "EditMode";

            if (string.IsNullOrEmpty(resultPath))
            {
                Debug.LogError("[UnityCoder] -unityCoderResult was not supplied.");
                EditorApplication.Exit(2);
                return;
            }

            var api = ScriptableObject.CreateInstance<TestRunnerApi>();
            api.RegisterCallbacks(new Callbacks(resultPath));

            TestMode mode = string.Equals(platform, "PlayMode", StringComparison.OrdinalIgnoreCase)
                ? TestMode.PlayMode
                : TestMode.EditMode;

            api.Execute(new ExecutionSettings(new Filter { testMode = mode }));
        }

        static string GetArg(string name)
        {
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (string.Equals(args[i], name, StringComparison.Ordinal))
                    return args[i + 1];
            }
            return null;
        }

        class Callbacks : ICallbacks
        {
            readonly string _resultPath;

            public Callbacks(string resultPath) => _resultPath = resultPath;

            public void RunStarted(ITestAdaptor testsToRun) { }

            public void RunFinished(ITestResultAdaptor result)
            {
                var failing = new List<string>();
                CollectFailures(result, failing);

                int total = result.PassCount + result.FailCount + result.SkipCount + result.InconclusiveCount;
                string json = BuildJson(total, result.FailCount, failing);

                try
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(_resultPath) ?? ".");
                    File.WriteAllText(_resultPath, json, Encoding.UTF8);
                }
                catch (Exception e)
                {
                    Debug.LogError("[UnityCoder] failed to write result: " + e);
                    EditorApplication.Exit(3);
                    return;
                }

                Debug.Log($"[UnityCoder] total={total} failed={result.FailCount}");
                EditorApplication.Exit(result.FailCount > 0 ? 1 : 0);
            }

            public void TestStarted(ITestAdaptor test) { }
            public void TestFinished(ITestResultAdaptor result) { }

            static void CollectFailures(ITestResultAdaptor node, List<string> sink)
            {
                if (node == null) return;

                bool failed = string.Equals(node.TestStatus.ToString(), "Failed", StringComparison.OrdinalIgnoreCase)
                    || (node.ResultState != null && node.ResultState.Status == TestStatus.Failed);

                if (failed && !node.HasChildren)
                {
                    sink.Add(node.FullName ?? node.Name ?? "<unnamed>");
                }

                if (node.Children == null) return;
                foreach (var child in node.Children)
                    CollectFailures(child, sink);
            }

            static string BuildJson(int total, int failed, List<string> failingTests)
            {
                var sb = new StringBuilder();
                sb.Append('{');
                sb.Append("\"tests_total\":").Append(total.ToString(CultureInfo.InvariantCulture)).Append(',');
                sb.Append("\"tests_failed\":").Append(failed.ToString(CultureInfo.InvariantCulture)).Append(',');
                sb.Append("\"failing_tests\":[");
                for (int i = 0; i < failingTests.Count; i++)
                {
                    if (i > 0) sb.Append(',');
                    sb.Append('"').Append(Escape(failingTests[i])).Append('"');
                }
                sb.Append("]}");
                return sb.ToString();
            }

            static string Escape(string value)
            {
                var sb = new StringBuilder(value.Length + 8);
                foreach (char c in value)
                {
                    switch (c)
                    {
                        case '"': sb.Append("\\\""); break;
                        case '\\': sb.Append("\\\\"); break;
                        case '\n': sb.Append("\\n"); break;
                        case '\r': sb.Append("\\r"); break;
                        case '\t': sb.Append("\\t"); break;
                        default:
                            if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                            else sb.Append(c);
                            break;
                    }
                }
                return sb.ToString();
            }
        }
    }
}
