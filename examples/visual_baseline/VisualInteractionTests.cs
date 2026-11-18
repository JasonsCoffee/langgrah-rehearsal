using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Events;
using FrameworkVisualDemo;

namespace FrameworkVisualDemo.Tests
{
    public sealed class Interactions
    {
        const string Prefab = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab";

        [Test] public void ConfirmUsesThePreparedBindingToShowReady()
        {
            var instance = Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(Prefab));
            try
            {
                var shell = instance.GetComponent<ExpeditionPreviewShell>();
                shell.confirmButton.onClick.SetPersistentListenerState(0, UnityEventCallState.EditorAndRuntime);
                shell.confirmButton.onClick.Invoke();
                Assert.AreEqual("READY FOR REVIEW", shell.statusText.text);
                Assert.AreEqual((Color)new Color32(166,231,199,255), shell.statusText.color);
            }
            finally { Object.DestroyImmediate(instance); }
        }

        [Test] public void ResetRestoresThePreparedPreviewState()
        {
            var instance = Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(Prefab));
            try
            {
                var shell = instance.GetComponent<ExpeditionPreviewShell>();
                shell.resetButton.onClick.SetPersistentListenerState(0, UnityEventCallState.EditorAndRuntime);
                shell.statusText.text = "DIRTY PREVIEW";
                shell.statusText.color = Color.white;
                shell.resetButton.onClick.Invoke();
                Assert.AreEqual("BASELINE PREVIEW", shell.statusText.text);
                Assert.AreEqual((Color)new Color32(246,169,139,255), shell.statusText.color);
            }
            finally { Object.DestroyImmediate(instance); }
        }
    }
}
