using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using FrameworkVisualDemo;

namespace FrameworkVisualDemo.Tests
{
    public sealed class CoralPresentation
    {
        [Test] public void PrimaryButtonUsesTheRequestedWarmCoral()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(
                "Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab");
            var shell = prefab.GetComponent<ExpeditionPreviewShell>();
            Assert.AreEqual((Color)new Color32(246,169,139,255), shell.confirmButton.image.color);
            Assert.AreEqual((Color)new Color32(34,52,65,255), shell.resetButton.image.color);
        }
    }
}
