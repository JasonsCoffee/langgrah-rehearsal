using NUnit.Framework;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

namespace FrameworkVisualDemo.Tests
{
    public sealed class Preparation
    {
        const string Root = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/";
        const string Prefab = Root + "UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab";
        const string Scene = Root + "Scenes/FrameworkVisualDemo/VisualBaseline.unity";

        [Test] public void PrefabHasNoMissingScriptsAndAllExplicitBindingsResolve()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Prefab);
            Assert.NotNull(prefab, "Architect must create the isolated prefab before freeze");
            foreach (var node in prefab.GetComponentsInChildren<Transform>(true))
                Assert.AreEqual(0, GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject));
            var shell = prefab.GetComponent("ExpeditionPreviewShell");
            Assert.NotNull(shell);
            var serialized = new SerializedObject(shell);
            foreach (var field in new[] { "confirmButton", "resetButton", "statusText", "heroImage" })
                Assert.NotNull(serialized.FindProperty(field)?.objectReferenceValue, field);
            var confirm = (Button)serialized.FindProperty("confirmButton").objectReferenceValue;
            Assert.AreEqual(1, confirm.onClick.GetPersistentEventCount());
            Assert.AreEqual(shell, confirm.onClick.GetPersistentTarget(0));
            Assert.AreEqual("PreviewReady", confirm.onClick.GetPersistentMethodName(0));
        }

        [Test] public void PlaceholderImportsWithArtistDimensionsAndStableSpriteIdentity()
        {
            string path = Root + "UI/Images/FrameworkVisualDemo/expedition_placeHolder.png";
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            Assert.NotNull(sprite);
            Assert.AreEqual(new Vector2(768, 480), sprite.rect.size);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            Assert.AreEqual(TextureImporterType.Sprite, importer.textureType);
            Assert.AreEqual(SpriteImportMode.Single, importer.spriteImportMode);
            Assert.IsFalse(importer.mipmapEnabled);
            Assert.IsTrue(importer.sRGBTexture);
            Assert.AreEqual(TextureImporterCompression.Uncompressed, importer.textureCompression);
        }

        [Test] public void ReviewSceneLoadsItsPrefabWithoutGameBootstrap()
        {
            Assert.NotNull(AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene));
            var scene = EditorSceneManager.OpenScene(Scene, OpenSceneMode.Additive);
            try
            {
                bool found = false;
                foreach (var root in scene.GetRootGameObjects())
                {
                    Assert.IsFalse(root.name.Contains("Monopoly"));
                    foreach (var node in root.GetComponentsInChildren<Transform>(true))
                    {
                        Assert.AreEqual(0, GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject));
                        if (PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(node.gameObject) == Prefab)
                            found = true;
                    }
                }
                Assert.IsTrue(found, "Scene must reference the actual prepared prefab");
            }
            finally { EditorSceneManager.CloseScene(scene, true); }
        }
    }
}
