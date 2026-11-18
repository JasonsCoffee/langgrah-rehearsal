// Architect-only preparation for the isolated fixture. Never invoked by coding units.
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using FrameworkVisualDemo;
using jj.UnityOperator.Editor;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace UnityCoder
{
    public sealed class FrameworkPrepareVisualCommand : IUnityOpCommand
    {
        public string CommandName => "FrameworkPrepareVisual";
        public string Execute(string json)
        {
            try { return CommandResult.SuccessWithData(FrameworkVisualPreparation.Execute(
                (string)JObject.Parse(json)["operation"]).ToString()).ToJson(); }
            catch (Exception error) { return CommandResult.Error(error.Message).ToJson(); }
        }
    }

    public static class FrameworkVisualPreparation
    {
        const string Game = "Assets/JJGame/monopoly/";
        const string Resource = Game + "Runtime/Resource/monopoly/";
        const string Prefab = Resource + "UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab";
        const string ScenePath = Resource + "Scenes/FrameworkVisualDemo/VisualBaseline.unity";
        const string Artwork = Resource + "UI/Images/FrameworkVisualDemo/expedition_placeHolder.png";
        const string Output = ".agent/visual-baseline";
        static Color Navy => new Color32(17, 30, 43, 255);
        static Color Cream => new Color32(245, 241, 224, 255);
        static Color Mint => new Color32(166, 231, 199, 255);

        public static JObject Execute(string operation)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
                throw new InvalidOperationException("Preparation requires idle Edit Mode");
            if (operation == "create") Create();
            else if (operation == "open")
            {
                if (Enumerable.Range(0, SceneManager.sceneCount).Any(i => SceneManager.GetSceneAt(i).isDirty))
                    throw new InvalidOperationException("Save or close dirty scenes before opening the review scene");
            }
            else if (operation != "inspect") throw new ArgumentException("Use create, inspect or open");
            var report = Inspect();
            Directory.CreateDirectory(Output);
            File.WriteAllText(Output + "/editor-report.json", report.ToString());
            if (operation == "open")
            {
                EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
                EditorApplication.ExecuteMenuItem("Window/General/Game");
            }
            return report;
        }

        static void Create()
        {
            // Never regenerate over reviewed or partially prepared assets.
            foreach (string path in new[] { Prefab, ScenePath, Artwork })
                if (File.Exists(path) || File.Exists(path + ".meta"))
                    throw new InvalidOperationException("Preparation destination already exists: " + path);
            foreach (string path in new[] { Prefab, ScenePath, Artwork })
                Directory.CreateDirectory(Path.GetDirectoryName(path));
            CreateArtwork();
            AssetDatabase.Refresh();
            var importer = (TextureImporter)AssetImporter.GetAtPath(Artwork);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 100;
            importer.mipmapEnabled = false;
            importer.sRGBTexture = true;
            importer.alphaIsTransparency = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
            var previous = SceneManager.GetActiveScene();
            SceneManager.SetActiveScene(scene);
            try
            {
                var canvasObject = new GameObject("ReviewCanvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
                var canvas = canvasObject.GetComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                var scaler = canvasObject.GetComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1080, 2160);
                scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
                scaler.matchWidthOrHeight = 1;
                var root = Panel("ExpeditionBriefing", canvas.transform, 0, 0, 1080, 2160, Navy);
                var rootRect = root.GetComponent<RectTransform>();
                rootRect.anchorMin = rootRect.anchorMax = new Vector2(.5f, 1);
                rootRect.anchoredPosition = new Vector2(-540,0);
                var shell = root.AddComponent<ExpeditionPreviewShell>();
                Label("Eyebrow", root.transform, "F I E L D   N O T E S     /     0 1", 90, 140, 900, 50, 27, Mint);
                Label("Title", root.transform, "Expedition\nbriefing", 90, 230, 900, 220, 92, Cream);
                Label("Subtitle", root.transform, "A small journey. A new perspective.", 94, 475, 890, 65, 32, new Color32(168,185,190,255));
                var hero = Panel("Landscape", root.transform, 90, 600, 900, 562.5f, Color.white).GetComponent<Image>();
                hero.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(Artwork);
                hero.preserveAspect = true;
                shell.heroImage = hero;
                Label("DestinationLabel", root.transform, "NEXT DESTINATION", 94, 1225, 890, 40, 24, Mint);
                Label("Destination", root.transform, "Northern Ridge", 90, 1280, 900, 85, 60, Cream);
                Panel("Divider", root.transform, 90, 1410, 900, 2, new Color32(58,77,87,255));
                Metric(root.transform, "Explorers", "02", "EXPLORERS", 90);
                Metric(root.transform, "Duration", "15 min", "DURATION", 400);
                Metric(root.transform, "Reward", "+120", "CREDITS", 710);
                shell.statusText = Label("Status", root.transform, "BASELINE PREVIEW", 90, 1640, 900, 60, 27, new Color32(246,169,139,255));
                shell.confirmButton = Button("Confirm", root.transform, "Preview ready state", 90, 1760, Mint, Navy);
                shell.resetButton = Button("Reset", root.transform, "Reset preview", 90, 1900, new Color32(34,52,65,255), Cream);
                UnityEventTools.AddPersistentListener(shell.confirmButton.onClick, shell.PreviewReady);
                UnityEventTools.AddPersistentListener(shell.resetButton.onClick, shell.ResetPreview);
                Label("Footer", root.transform, "VISUAL BASELINE  /  PLACEHOLDER ART", 90, 2070, 900, 35, 20, new Color32(142,160,170,255));
                PrefabUtility.SaveAsPrefabAssetAndConnect(root, Prefab, InteractionMode.AutomatedAction);
                var cameraObject = new GameObject("PreviewCamera", typeof(Camera));
                var camera = cameraObject.GetComponent<Camera>();
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = Navy;
                camera.cullingMask = 0;
                new GameObject("PreviewEventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
                if (!EditorSceneManager.SaveScene(scene, ScenePath)) throw new IOException("Review scene save failed");
                AssetDatabase.SaveAssets();
            }
            finally
            {
                SceneManager.SetActiveScene(previous);
                EditorSceneManager.CloseScene(scene, true);
            }
        }

        static GameObject Panel(string name, Transform parent, float x, float y, float w, float h, Color color)
        {
            var node = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
            node.transform.SetParent(parent, false);
            Rect(node.GetComponent<RectTransform>(), x, y, w, h);
            node.GetComponent<Image>().color = color;
            node.GetComponent<Image>().raycastTarget = false;
            return node;
        }

        static void Rect(RectTransform rect, float x, float y, float w, float h)
        {
            rect.anchorMin = rect.anchorMax = new Vector2(0, 1);
            rect.pivot = new Vector2(0, 1);
            rect.anchoredPosition = new Vector2(x, -y);
            rect.sizeDelta = new Vector2(w, h);
        }

        static Text Label(string name, Transform parent, string content, float x, float y, float w, float h, int size, Color color)
        {
            var node = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Text));
            node.transform.SetParent(parent, false);
            Rect(node.GetComponent<RectTransform>(), x, y, w, h);
            var text = node.GetComponent<Text>();
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.text = content; text.fontSize = size; text.color = color;
            text.alignment = TextAnchor.MiddleLeft;
            text.raycastTarget = false;
            return text;
        }

        static Button Button(string name, Transform parent, string content, float x, float y, Color background, Color foreground)
        {
            var node = Panel(name, parent, x, y, 900, 112, background);
            node.GetComponent<Image>().raycastTarget = true;
            var button = node.AddComponent<Button>();
            button.targetGraphic = node.GetComponent<Image>();
            var text = Label("Label", node.transform, content, 0, 0, 900, 112, 34, foreground);
            text.alignment = TextAnchor.MiddleCenter;
            return button;
        }

        static void Metric(Transform parent, string name, string value, string caption, float x)
        {
            Label(name, parent, value, x, 1470, 280, 75, 52, Cream);
            Label(name + "Caption", parent, caption, x, 1550, 280, 40, 22, new Color32(168,185,190,255));
        }

        static void CreateArtwork()
        {
            var texture = new Texture2D(768, 480, TextureFormat.RGB24, false);
            try
            {
                for (int y = 0; y < 480; y++) for (int x = 0; x < 768; x++)
                {
                    Color color = Color.Lerp(new Color32(59,106,118,255), new Color32(33,58,79,255), y/480f);
                    if ((x-557)*(x-557)+(y-350)*(y-350) < 64*64) color = new Color32(245,216,166,255);
                    if (y < 350 - Math.Abs(x-260)*.85f) color = new Color32(106,156,160,255);
                    if (y < 310 - Math.Abs(x-510)*.9f) color = new Color32(68,117,126,255);
                    if (y < 235 - Math.Abs(x-150)*.55f) color = new Color32(35,76,91,255);
                    if (y < 165 - Math.Abs(x-570)*.3f) color = new Color32(23,51,67,255);
                    texture.SetPixel(x,y,color);
                }
                texture.Apply();
                File.WriteAllBytes(Artwork, texture.EncodeToPNG());
            }
            finally { UnityEngine.Object.DestroyImmediate(texture); }
        }

        static JObject Inspect()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Prefab);
            if (prefab == null) throw new InvalidOperationException("Prepared prefab is missing");
            var shell = prefab.GetComponent<ExpeditionPreviewShell>();
            var missing = new JArray(); var unresolved = new JArray(); var hierarchy = new JArray(); var bindings = new JArray();
            foreach (var node in prefab.GetComponentsInChildren<Transform>(true))
            {
                string path = node == prefab.transform ? "." : AnimationUtility.CalculateTransformPath(node, prefab.transform);
                hierarchy.Add(path);
                if (GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject) != 0) missing.Add(path);
            }
            if (shell == null) unresolved.Add("ExpeditionPreviewShell");
            else
            {
                var serialized = new SerializedObject(shell);
                foreach (string field in new[] { "confirmButton", "resetButton", "statusText", "heroImage" })
                {
                    var value = serialized.FindProperty(field)?.objectReferenceValue as Component;
                    if (value == null || !value.transform.IsChildOf(prefab.transform)) unresolved.Add(field);
                    else bindings.Add(new JArray("FrameworkVisualDemo.ExpeditionPreviewShell." + field,
                        AnimationUtility.CalculateTransformPath(value.transform,prefab.transform)));
                }
                CheckClick(shell.confirmButton, shell, "PreviewReady", unresolved);
                CheckClick(shell.resetButton, shell, "ResetPreview", unresolved);
            }
            // Reuse the installed game's read-only PSD/prefab inspector. No PSD is invented.
            Type inspector = AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType(
                "jj.Monopoly.Editor.Psd2UIFormSpec.PsdPrefabLayoutAutomation")).FirstOrDefault(t => t != null);
            if (inspector == null) throw new InvalidOperationException("Existing prefab inspector is unavailable");
            string layoutJson = (string)inspector.GetMethod("Execute", BindingFlags.Public|BindingFlags.Static).Invoke(null,
                new object[] { new JObject { ["operation"]="InspectPrefabLayout", ["prefabPath"]=Prefab }.ToString() });
            var layout = JObject.Parse(layoutJson);
            if ((string)layout["status"] != "success") throw new InvalidOperationException("Existing prefab layout inspection failed: " + layout);
            var ids = new JArray(); var serializedIds = new JArray();
            foreach (string path in new[] { ScenePath, Prefab, Artwork })
            {
                string guid = AssetDatabase.AssetPathToGUID(path);
                if (AssetDatabase.GUIDToAssetPath(guid) != path) throw new InvalidOperationException("Asset GUID round-trip failed");
                var serializedGuid = Regex.Match(File.ReadAllText(path + ".meta"), @"(?m)^guid:\s*(\S+)\s*$");
                if (!serializedGuid.Success) throw new InvalidOperationException("Missing serialized GUID");
                ids.Add(new JArray(path.Substring(Game.Length), guid));
                serializedIds.Add(new JArray(path.Substring(Game.Length), serializedGuid.Groups[1].Value));
            }
            var importer = AssetImporter.GetAtPath(Artwork) as TextureImporter;
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(Artwork);
            bool imported = importer != null && sprite != null && sprite.rect.size == new Vector2(768,480)
                && importer.textureType == TextureImporterType.Sprite && importer.spriteImportMode == SpriteImportMode.Single
                && !importer.mipmapEnabled && importer.sRGBTexture && importer.textureCompression == TextureImporterCompression.Uncompressed;
            if (!imported) unresolved.Add("placeholder import requirements");
            bool sceneLoaded = false;
            var scene = SceneManager.GetSceneByPath(ScenePath);
            bool openedForInspection = !scene.IsValid() || !scene.isLoaded;
            if (openedForInspection) scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Additive);
            try
            {
                sceneLoaded = scene.GetRootGameObjects().SelectMany(g => g.GetComponentsInChildren<ExpeditionPreviewShell>(true)).Count() == 1;
                foreach (var node in scene.GetRootGameObjects().SelectMany(g => g.GetComponentsInChildren<Transform>(true)))
                    if (GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject) != 0) missing.Add(node.name);
            }
            finally { if (openedForInspection) EditorSceneManager.CloseScene(scene, true); }
            var files = new JArray();
            foreach (string directory in new[] { "Runtime/Script/FrameworkVisualDemo", "Runtime/Resource/monopoly/UI/Prefabs/FrameworkVisualDemo",
                "Runtime/Resource/monopoly/UI/Images/FrameworkVisualDemo", "Runtime/Resource/monopoly/Scenes/FrameworkVisualDemo",
                "Editor/ArtSource~/FrameworkVisualDemo" })
            {
                if (File.Exists(Game + directory + ".meta")) files.Add(new JArray(directory + ".meta", Hash(Game + directory + ".meta")));
                foreach (string filename in Directory.GetFiles(Game + directory, "*", SearchOption.AllDirectories).OrderBy(p => p, StringComparer.Ordinal))
                    files.Add(new JArray(filename.Replace('\\','/').Substring(Game.Length), Hash(filename)));
            }
            return new JObject { ["revision"]="visual-baseline-v1", ["files"]=files,
                ["entries"]=new JArray(ScenePath.Substring(Game.Length), Prefab.Substring(Game.Length)),
                ["missing_scripts"]=missing, ["unresolved_bindings"]=unresolved, ["asset_ids"]=ids, ["serialized_asset_ids"]=serializedIds,
                ["bindings"]=bindings, ["hierarchy"]=hierarchy, ["launchable"]=sceneLoaded && missing.Count==0 && unresolved.Count==0,
                ["layout"]=layout, ["import_settings"]=new JObject { ["width"]=768,["height"]=480,["type"]="Sprite Single",["mipmaps"]=false,["sRGB"]=true,["compression"]="Uncompressed" } };
        }

        static void CheckClick(Button button, ExpeditionPreviewShell shell, string method, JArray errors)
        {
            if (button == null || button.onClick.GetPersistentEventCount()!=1 || button.onClick.GetPersistentTarget(0)!=shell
                || button.onClick.GetPersistentMethodName(0)!=method) errors.Add(method);
        }

        static string Hash(string path)
        {
            using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
        }
    }
}
