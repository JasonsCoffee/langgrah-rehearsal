using System;
using System.IO;
using System.Security.Cryptography;
using FrameworkVisualDemo;
using jj.UnityOperator.Editor;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;

namespace UnityCoder
{
    // Explicit Architect revision requested by the human, not a coder mutation tool.
    public sealed class FrameworkVisualCoralRevision : IUnityOpCommand
    {
        public string CommandName => "FrameworkVisualCoralRevision";
        const string Prefab = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab";
        const string Expected = "355d22c55060ff0258a2027875a0e8c1123d92846548335e0fff4d97f11e1d45";

        public string Execute(string json)
        {
            try
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
                    throw new InvalidOperationException("Revision requires idle Edit Mode");
                string hash;
                using (var sha=SHA256.Create()) hash=BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(Prefab))).Replace("-","").ToLowerInvariant();
                if (hash!=Expected) throw new InvalidOperationException("Expected the exact approved v1 prefab; revision is not replayable");
                string guid=AssetDatabase.AssetPathToGUID(Prefab);
                var root=PrefabUtility.LoadPrefabContents(Prefab);
                try
                {
                    var shell=root.GetComponent<ExpeditionPreviewShell>();
                    if (shell==null || shell.confirmButton==null) throw new InvalidOperationException("Missing approved binding");
                    shell.confirmButton.image.color=new Color32(246,169,139,255);
                    PrefabUtility.SaveAsPrefabAsset(root,Prefab);
                }
                finally { PrefabUtility.UnloadPrefabContents(root); }
                if (AssetDatabase.AssetPathToGUID(Prefab)!=guid) throw new InvalidOperationException("Prefab GUID changed");
                var report=FrameworkVisualPreparation.Execute("inspect");
                report["revision"]="visual-baseline-v2";
                File.WriteAllText(".agent/visual-baseline/editor-report.v2.json",report.ToString());
                return CommandResult.SuccessWithData(new JObject { ["revision"]="visual-baseline-v2",
                    ["primary_color"]="#F6A98B",["guid_preserved"]=true,["launchable"]=report["launchable"] }.ToString()).ToJson();
            }
            catch(Exception error) { return CommandResult.Error(error.Message).ToJson(); }
        }
    }
}
