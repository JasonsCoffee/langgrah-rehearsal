// Architect-only construction of original placeholder assets and binding shells.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using jj.Reserve04.Runtime.LobbyRehearsal;
using jj.UnityOperator.Editor;
using Newtonsoft.Json.Linq;
using TMPro;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace MonopolyLobbyPreparation
{
    public sealed class PrepareLobbyCommand : IUnityOpCommand
    {
        public string CommandName => "PrepareMonopolyLobby";

        public string Execute(string json)
        {
            try
            {
                var request = JObject.Parse(json);
                return CommandResult.SuccessWithData(LobbyPreparation.Prepare((string)request["reportRoot"]).ToString()).ToJson();
            }
            catch (Exception error)
            {
                return CommandResult.Error(error.ToString()).ToJson();
            }
        }
    }

    public static class LobbyPreparation
    {
        const string Module = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/";
        const string Prefabs = Module + "UI/Prefabs/LobbyRehearsal/";
        const string Art = Prefabs + "Art/";
        const string ScenePath = Module + "Scenes/LobbyRehearsal/LobbyStreet_placeHolder.unity";
        static readonly string[] Screens = { "Lobby", "Appearance", "Friends", "Shop", "Records", "Chat", "Recharge", "Settings", "Handoff", "PlatformHome" };
        static readonly Color Ink = new Color32(26, 39, 53, 255);
        static readonly Color Cream = new Color32(249, 242, 225, 255);
        static readonly Color Coral = new Color32(217, 106, 73, 255);
        static readonly Color Blue = new Color32(57, 111, 145, 255);
        static readonly List<string> Created = new List<string>();
        static TMP_FontAsset font;

        public static JObject Prepare(string reportRoot)
        {
            if (string.IsNullOrWhiteSpace(reportRoot)) throw new ArgumentException("Trusted report directory required");
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
                throw new InvalidOperationException("Preparation requires idle Edit Mode");
            if (File.Exists(ScenePath) || Directory.Exists(Prefabs))
                throw new InvalidOperationException("Presentation destination already exists; reconcile before retry");
            Created.Clear();
            Directory.CreateDirectory(Art);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            var existing = AssetDatabase.LoadAssetAtPath<GameObject>(Module + "UI/Prefabs/Game/MatchView_placeHolder.prefab");
            var existingText = existing == null ? null : existing.GetComponentsInChildren<TextMeshProUGUI>(true).FirstOrDefault(t => t.font != null);
            var sourceFont = existingText == null ? TMP_Settings.defaultFontAsset : existingText.font;
            if (sourceFont == null) throw new InvalidOperationException("Existing UI font unavailable");
            var fontPath = Art + "LobbyFont_placeHolder.asset";
            if (!AssetDatabase.CopyAsset(AssetDatabase.GetAssetPath(sourceFont), fontPath))
                throw new InvalidOperationException("Unable to prepare local font asset");
            font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(fontPath);
            // Freeze a private copy so inspection never writes a shared font asset.
            font.atlasPopulationMode = AtlasPopulationMode.Static;
            EditorUtility.SetDirty(font);
            AssetDatabase.SaveAssetIfDirty(font);
            Created.Add(fontPath);

            var cream = Material("Stone", new Color32(219, 200, 168, 255));
            var brick = Material("Brick", new Color32(166, 75, 53, 255));
            var navy = Material("Navy", Ink);
            var glass = Material("Glass", new Color32(113, 161, 176, 255));
            var road = Material("Road", new Color32(99, 108, 111, 255));
            var gold = Material("Brass", new Color32(212, 167, 80, 255));
            var black = Material("Rubber", new Color32(35, 38, 43, 255));
            var controller = Animations();
            var skins = new List<GameObject>();
            var colors = new[] { Blue, Coral, new Color(.25f, .48f, .35f), new Color(.68f, .5f, .7f), new Color(.78f, .64f, .3f), new Color(.32f, .48f, .66f) };
            for (var i = 0; i < 6; i++) skins.Add(Character(i, Material("Outfit" + i, colors[i]), navy, cream, controller));
            var vehicles = new List<GameObject>();
            for (var i = 0; i < 4; i++) vehicles.Add(Vehicle(i, Material("Paint" + i, colors[i]), black, glass, gold));
            var configuration = ScriptableObject.CreateInstance<LobbyConfiguration>();
            for (var i = 0; i < skins.Count; i++)
                configuration.Catalog.Add(new LobbyCatalogDefinition
                {
                    Id = "skin-" + i, Name = "街区居民 " + (i + 1), Kind = "skin",
                    Gender = i < 2 ? "any" : i % 2 == 0 ? "male" : "female",
                    UnlockType = i < 2 ? 1 : 0, ShopPriority = 100 - i,
                    Price = i < 2 ? 0 : i >= 4 ? 300 : 1000,
                    DurationDays = i >= 4 ? 7 : 0, Prefab = skins[i], Thumbnail = Thumbnail(skins[i], "Skin" + i)
                });
            for (var i = 0; i < vehicles.Count; i++)
                configuration.Catalog.Add(new LobbyCatalogDefinition
                {
                    Id = "vehicle-" + i, Name = "街区座驾 " + (i + 1), Kind = "vehicle", Gender = "any",
                    UnlockType = i == 0 ? 1 : 0, ShopPriority = 100 - i,
                    Price = i == 0 ? 0 : i == 2 ? 900 : 3000,
                    DurationDays = i == 2 ? 7 : 0, Prefab = vehicles[i], Thumbnail = Thumbnail(vehicles[i], "Vehicle" + i)
                });
            configuration.Catalog.Add(new LobbyCatalogDefinition
            {
                Id = "vehicle-none", Name = "无座驾", Kind = "vehicle", Gender = "any", UnlockType = 1
            });
            var configurationPath = Art + "LobbyConfiguration_placeHolder.asset";
            AssetDatabase.CreateAsset(configuration, configurationPath);
            Created.Add(configurationPath);

            var prior = SceneManager.GetActiveScene();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
            try
            {
                var root = new GameObject("LobbyStreet");
                var binding = root.AddComponent<LobbyStreetBinding>();
                Part(root.transform, "Road", PrimitiveType.Cube, new Vector3(0, -.15f, 5), new Vector3(10, .3f, 34), road);
                for (var side = -1; side <= 1; side += 2)
                {
                    Part(root.transform, "Pavement", PrimitiveType.Cube, new Vector3(side * 5.1f, .05f, 5), new Vector3(2.4f, .25f, 34), cream);
                    for (var block = 0; block < 5; block++)
                    {
                        var z = block * 5f - 3;
                        var height = 4.2f + block % 3 * .65f;
                        Part(root.transform, "WesternFacade_" + side + "_" + block, PrimitiveType.Cube,
                            new Vector3(side * 7, height / 2, z), new Vector3(3.2f, height, 4.6f), block % 2 == 0 ? brick : cream);
                        Part(root.transform, "Cornice", PrimitiveType.Cube, new Vector3(side * 7, height + .1f, z), new Vector3(3.5f, .25f, 4.85f), cream);
                        for (var level = 0; level < 2; level++)
                            for (var window = 0; window < 3; window++)
                                Part(root.transform, "Window", PrimitiveType.Cube,
                                    new Vector3(side * 5.35f, 1.35f + level * 1.65f, z - 1.4f + window * 1.4f), new Vector3(.12f, 1.1f, .8f), glass);
                        Part(root.transform, "StripedAwning", PrimitiveType.Cube, new Vector3(side * 5.1f, 2.6f, z), new Vector3(1.2f, .15f, 4.1f), block % 2 == 0 ? navy : gold);
                        Part(root.transform, "LampPost", PrimitiveType.Cylinder, new Vector3(side * 4.2f, 1.55f, z + 2), new Vector3(.1f, 1.55f, .1f), navy);
                        Part(root.transform, "Lamp", PrimitiveType.Sphere, new Vector3(side * 4.2f, 3.2f, z + 2), Vector3.one * .3f, gold);
                    }
                }
                var cameraNode = new GameObject("LobbyWorldCamera", typeof(Camera));
                cameraNode.transform.SetParent(root.transform, false);
                cameraNode.transform.position = new Vector3(0, 2.6f, -8.5f);
                cameraNode.transform.LookAt(new Vector3(0, 1.2f, 1.5f));
                binding.WorldCamera = cameraNode.GetComponent<Camera>();
                binding.WorldCamera.fieldOfView = 35;
                binding.WorldCamera.backgroundColor = new Color(.55f, .73f, .84f);
                binding.WorldCamera.clearFlags = CameraClearFlags.SolidColor;
                binding.WorldCamera.enabled = false;
                var lightNode = new GameObject("AfternoonSun", typeof(Light));
                lightNode.transform.SetParent(root.transform, false);
                lightNode.transform.rotation = Quaternion.Euler(45, -35, 0);
                lightNode.GetComponent<Light>().type = LightType.Directional;
                lightNode.GetComponent<Light>().intensity = 1.15f;
                lightNode.GetComponent<Light>().shadows = LightShadows.Soft;
                binding.CharacterMount = new GameObject("CharacterMount").transform;
                binding.CharacterMount.SetParent(root.transform, false);
                binding.CharacterMount.localPosition = new Vector3(0, .5f, 0);
                binding.VehicleMount = new GameObject("VehicleMount").transform;
                binding.VehicleMount.SetParent(root.transform, false);
                var character = (GameObject)PrefabUtility.InstantiatePrefab(skins[0], scene);
                character.transform.SetParent(binding.CharacterMount, false);
                binding.CharacterAnimator = character.GetComponent<Animator>();
                var vehicle = (GameObject)PrefabUtility.InstantiatePrefab(vehicles[0], scene);
                vehicle.transform.SetParent(binding.VehicleMount, false);
                binding.SkinPrefabs = skins;
                binding.VehiclePrefabs = vehicles;
                binding.Configuration = configuration;
                EditorSceneManager.SaveScene(scene, ScenePath);
                Created.Add(ScenePath);
            }
            finally
            {
                EditorSceneManager.CloseScene(scene, true);
                if (prior.IsValid() && prior.isLoaded) SceneManager.SetActiveScene(prior);
            }
            foreach (var screen in Screens) CreateView(screen);
            AssetDatabase.Refresh();
            var result = Inspect();
            Directory.CreateDirectory(reportRoot);
            File.WriteAllText(Path.Combine(reportRoot, "presentation-preparation.json"), result.ToString());
            return result;
        }

        static Material Material(string name, Color color)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            if (shader == null) throw new InvalidOperationException("A supported material shader is required");
            var value = new Material(shader) { name = name, color = color };
            var path = Art + name + "_placeHolder.mat";
            AssetDatabase.CreateAsset(value, path);
            Created.Add(path);
            return value;
        }

        static GameObject Part(Transform parent, string name, PrimitiveType shape, Vector3 position, Vector3 scale, Material material)
        {
            var node = GameObject.CreatePrimitive(shape);
            node.name = name;
            node.transform.SetParent(parent, false);
            node.transform.localPosition = position;
            node.transform.localScale = scale;
            node.GetComponent<Renderer>().sharedMaterial = material;
            UnityEngine.Object.DestroyImmediate(node.GetComponent<Collider>());
            return node;
        }

        static GameObject Character(int index, Material outfit, Material dark, Material skin, AnimatorController controller)
        {
            var root = new GameObject("Skin" + index);
            try
            {
                var body = new GameObject("BodyRoot").transform;
                body.SetParent(root.transform, false);
                Part(body, "Torso", PrimitiveType.Capsule, new Vector3(0, .88f, 0), new Vector3(.5f, .45f, .32f), outfit);
                Part(body, "Head", PrimitiveType.Sphere, new Vector3(0, 1.55f, 0), new Vector3(.66f, .72f, .6f), skin);
                Part(body, "Hair", PrimitiveType.Sphere, new Vector3(0, 1.77f, .02f), new Vector3(.68f, .3f, .6f), dark);
                for (var side = -1; side <= 1; side += 2)
                {
                    Part(body, "Eye", PrimitiveType.Sphere, new Vector3(side * .14f, 1.57f, -.275f), new Vector3(.07f, .1f, .05f), dark);
                    Part(body, side < 0 ? "LeftLeg" : "RightLeg", PrimitiveType.Capsule, new Vector3(side * .15f, .3f, 0), new Vector3(.19f, .3f, .2f), dark);
                    var arm = new GameObject(side < 0 ? "LeftArm" : "RightArm").transform;
                    arm.SetParent(body, false);
                    arm.localPosition = new Vector3(side * .35f, 1.1f, 0);
                    Part(arm, "Sleeve", PrimitiveType.Capsule, new Vector3(0, -.2f, 0), new Vector3(.16f, .27f, .16f), outfit);
                    Part(arm, "Hand", PrimitiveType.Sphere, new Vector3(0, -.48f, 0), Vector3.one * .18f, skin);
                }
                root.AddComponent<Animator>().runtimeAnimatorController = controller;
                var path = Art + "Skin" + index + "_placeHolder.prefab";
                var prefab = PrefabUtility.SaveAsPrefabAsset(root, path);
                Created.Add(path);
                return prefab;
            }
            finally { UnityEngine.Object.DestroyImmediate(root); }
        }

        static GameObject Vehicle(int index, Material paint, Material rubber, Material glass, Material brass)
        {
            var root = new GameObject("Vehicle" + index);
            try
            {
                Part(root.transform, "Body", PrimitiveType.Cube, new Vector3(0, .4f, 0), new Vector3(1.25f, .35f, 1.9f + .1f * index), paint);
                Part(root.transform, "Cabin", PrimitiveType.Cube, new Vector3(0, .75f, .25f), new Vector3(.95f, .5f + .1f * index, .9f), glass);
                Part(root.transform, "Bonnet", PrimitiveType.Cube, new Vector3(0, .58f, -.65f), new Vector3(1.1f, .12f, .6f), paint);
                Part(root.transform, "Bumper", PrimitiveType.Cube, new Vector3(0, .35f, -1), new Vector3(1.3f, .12f, .12f), brass);
                var seat = new GameObject("SeatAnchor").transform;
                seat.SetParent(root.transform, false);
                seat.localPosition = new Vector3(0, .55f, .15f);
                for (var side = -1; side <= 1; side += 2)
                    for (var axle = -1; axle <= 1; axle += 2)
                    {
                        var wheel = Part(root.transform, "Wheel", PrimitiveType.Cylinder, new Vector3(side * .62f, .25f, axle * .65f), new Vector3(.5f, .12f, .5f), rubber);
                        wheel.transform.localRotation = Quaternion.Euler(0, 0, 90);
                    }
                var path = Art + "Vehicle" + index + "_placeHolder.prefab";
                var prefab = PrefabUtility.SaveAsPrefabAsset(root, path);
                Created.Add(path);
                return prefab;
            }
            finally { UnityEngine.Object.DestroyImmediate(root); }
        }

        static AnimatorController Animations()
        {
            var path = Art + "CharacterActions_placeHolder.controller";
            var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            controller.AddParameter("Action", AnimatorControllerParameterType.Int);
            var machine = controller.layers[0].stateMachine;
            for (var index = 0; index < 3; index++)
            {
                var clip = new AnimationClip { name = new[] { "Idle", "Wave", "Celebrate" }[index] };
                clip.SetCurve("BodyRoot", typeof(Transform), "localPosition.y", new AnimationCurve(
                    new Keyframe(0, 0), new Keyframe(.5f, index == 2 ? .12f : .035f), new Keyframe(1, 0)));
                if (index > 0) clip.SetCurve("BodyRoot/RightArm", typeof(Transform), "localEulerAnglesRaw.z", AnimationCurve.EaseInOut(0, 0, 1, 140));
                if (index == 2) clip.SetCurve("BodyRoot/LeftArm", typeof(Transform), "localEulerAnglesRaw.z", AnimationCurve.EaseInOut(0, 0, 1, -140));
                var settings = AnimationUtility.GetAnimationClipSettings(clip);
                settings.loopTime = true;
                AnimationUtility.SetAnimationClipSettings(clip, settings);
                var clipPath = Art + clip.name + "_placeHolder.anim";
                AssetDatabase.CreateAsset(clip, clipPath);
                Created.Add(clipPath);
                var state = machine.AddState(clip.name);
                state.motion = clip;
                var transition = machine.AddAnyStateTransition(state);
                transition.hasExitTime = false;
                transition.canTransitionToSelf = false;
                transition.duration = .15f;
                transition.AddCondition(AnimatorConditionMode.Equals, index, "Action");
                if (index == 0) machine.defaultState = state;
            }
            AssetDatabase.SaveAssetIfDirty(controller);
            Created.Add(path);
            return controller;
        }

        static Sprite Thumbnail(GameObject prefab, string name)
        {
            var preview = new PreviewRenderUtility();
            Texture2D texture = null;
            try
            {
                var instance = UnityEngine.Object.Instantiate(prefab);
                preview.AddSingleGO(instance);
                preview.camera.orthographic = true;
                preview.camera.orthographicSize = name.StartsWith("Skin", StringComparison.Ordinal) ? 1.15f : 1.4f;
                preview.camera.transform.position = new Vector3(2.2f, 1.7f, -4);
                preview.camera.transform.LookAt(new Vector3(0, .85f, 0));
                preview.camera.backgroundColor = Ink;
                preview.camera.clearFlags = CameraClearFlags.SolidColor;
                preview.lights[0].intensity = 1.2f;
                preview.lights[0].transform.rotation = Quaternion.Euler(40, -25, 0);
                preview.lights[1].intensity = .6f;
                preview.BeginStaticPreview(new Rect(0, 0, 256, 320));
                preview.Render(true);
                texture = preview.EndStaticPreview();
                var path = Module + "UI/Images/LobbyRehearsal/" + name + "_placeHolder.png";
                File.WriteAllBytes(path, texture.EncodeToPNG());
                AssetDatabase.ImportAsset(path);
                var importer = (TextureImporter)AssetImporter.GetAtPath(path);
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.mipmapEnabled = false;
                importer.SaveAndReimport();
                Created.Add(path);
                return AssetDatabase.LoadAssetAtPath<Sprite>(path);
            }
            finally
            {
                if (texture != null) UnityEngine.Object.DestroyImmediate(texture);
                preview.Cleanup();
            }
        }

        static RectTransform Rect(string name, Transform parent, float x, float y, float width, float height)
        {
            var node = new GameObject(name, typeof(RectTransform));
            node.transform.SetParent(parent, false);
            var rect = node.GetComponent<RectTransform>();
            rect.anchorMin = rect.anchorMax = new Vector2(0, 1);
            rect.pivot = new Vector2(0, 1);
            rect.anchoredPosition = new Vector2(x, -y);
            rect.sizeDelta = new Vector2(width, height);
            return rect;
        }

        static TextMeshProUGUI Label(Transform parent, string text, float width, float height, int size)
        {
            var rect = Rect("Label", parent, 10, 0, width - 20, height);
            var label = rect.gameObject.AddComponent<TextMeshProUGUI>();
            label.font = font;
            label.fontSize = size;
            label.text = text;
            label.color = Cream;
            label.alignment = TextAlignmentOptions.MidlineLeft;
            label.overflowMode = TextOverflowModes.Overflow;
            label.raycastTarget = false;
            return label;
        }

        static void Control(LobbyRehearsalViewBase view, Transform parent, string action, string caption, float x, float y, float width, float height, bool primary = false)
        {
            var rect = Rect(action, parent, x, y, width, height);
            var image = rect.gameObject.AddComponent<Image>();
            image.color = primary ? Coral : Blue;
            var button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            var label = Label(rect, caption, width, height, primary ? 40 : 30);
            label.alignment = TextAlignmentOptions.Center;
            view.Controls.Add(new LobbyControlBinding { Action = action, Button = button, Label = label });
        }

        static void CreateView(string screen)
        {
            var root = Rect(screen + "View", null, 0, 0, 1080, 2160);
            try
            {
                var type = typeof(LobbyView).Assembly.GetType("jj.Reserve04.Runtime.LobbyRehearsal." + screen + "View", true);
                var view = (LobbyRehearsalViewBase)root.gameObject.AddComponent(type);
                view.SafeArea = Rect("SafeArea", root, 0, 0, 1080, 2160);
                var safe = view.SafeArea;
                view.Title = Label(Rect("Header", safe, 150, 30, 760, 90), screen, 760, 90, 42);
                view.Status = Label(Rect("Status", safe, 40, 140, 1000, 90), "", 1000, 90, 28);
                Control(view, safe, "Back", "返回", 30, 30, 110, 85);
                var preview = screen == "Lobby" || screen == "Appearance" || screen == "Shop";
                var scrollTop = preview ? 1130 : 290;
                var scrollHeight = preview ? 690 : 1530;
                var scrollNode = Rect("Scroll", safe, 40, scrollTop, 1000, scrollHeight);
                scrollNode.gameObject.AddComponent<Image>().color = new Color(Ink.r, Ink.g, Ink.b, .92f);
                var viewport = Rect("Viewport", scrollNode, 0, 0, 1000, scrollHeight);
                viewport.gameObject.AddComponent<RectMask2D>();
                var content = Rect("Content", viewport, 0, 0, 1000, 1450);
                view.Scroll = scrollNode.gameObject.AddComponent<ScrollRect>();
                view.Scroll.viewport = viewport;
                view.Scroll.content = content;
                view.Scroll.horizontal = false;
                for (var index = 0; index < 10; index++)
                {
                    Control(view, content, "Row" + index, "", 0, index * 145, 650, 130);
                    Control(view, content, "Secondary" + index, "", 665, index * 145, 165, 130);
                    Control(view, content, "Avatar" + index, "", 840, index * 145, 145, 130);
                }
                var inputNode = Rect("Input", safe, 40, 1840, 1000, 110);
                inputNode.gameObject.AddComponent<Image>().color = Ink;
                var inputText = Label(inputNode, "", 1000, 110, 32);
                view.Input = inputNode.gameObject.AddComponent<TMP_InputField>();
                view.Input.textViewport = inputNode;
                view.Input.textComponent = inputText;
                view.Input.richText = false;
                var common = new[] { "Primary", "Cancel", "Previous", "Next", "Tab0", "Tab1", "Tab2", "Confirm", "Decline", "Copy", "Paste", "Vip", "Rules", "About", "Support", "Music", "Effects", "Quality", "Report", "Send", "Complete", "Reconnect" };
                for (var index = 0; index < common.Length; index++)
                {
                    // Footer alternatives occupy declared state-dependent slots.
                    // SHELL binds visibility without changing serialized layout.
                    var action = common[index];
                    var tab = action.StartsWith("Tab", StringComparison.Ordinal);
                    var x = tab ? 40 + int.Parse(action.Substring(3)) * 340 : 40 + index % 4 * 255;
                    var y = tab ? scrollTop - 100 : 1980;
                    Control(view, safe, action, action, x, y, tab ? 325 : 240, 95, index == 0);
                    view.Controls.Last().Button.gameObject.SetActive(false);
                }
                if (screen == "Lobby")
                {
                    Control(view, safe, "Coins", "金币", 160, 30, 280, 85);
                    Control(view, safe, "Ingots", "元宝", 450, 30, 280, 85);
                    Control(view, safe, "Menu", "菜单", 890, 30, 150, 85);
                    Control(view, safe, "Appearance", "", 80, 260, 920, 800);
                    view.Controls.Last().Button.image.color = Color.clear;
                    Control(view, safe, "Marquee", "世界消息", 40, 1060, 1000, 65);
                    for (var index = 0; index < 5; index++)
                        Control(view, safe, "Tier" + index, "场次 " + (index + 1), 40 + index * 200, 1660, 190, 145);
                    Control(view, safe, "Chat", "聊天", 40, 1980, 180, 110);
                    Control(view, safe, "Invite", "邀请队友", 240, 1980, 240, 110);
                    Control(view, safe, "Start", "开始", 520, 1980, 520, 110, true);
                }
                var path = Prefabs + screen + "View_placeHolder.prefab";
                PrefabUtility.SaveAsPrefabAsset(root.gameObject, path);
                Created.Add(path);
            }
            finally { UnityEngine.Object.DestroyImmediate(root.gameObject); }
        }

        static JObject Inspect()
        {
            var views = new JArray();
            foreach (var screen in Screens)
            {
                var path = Prefabs + screen + "View_placeHolder.prefab";
                var root = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                var view = root.GetComponent<LobbyRehearsalViewBase>();
                if (view == null || view.Title == null || view.Input == null || view.Scroll == null || view.SafeArea == null)
                    throw new InvalidOperationException("Unresolved references: " + screen);
                foreach (var node in root.GetComponentsInChildren<Transform>(true))
                    if (GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject) > 0)
                        throw new InvalidOperationException("Missing script: " + path);
                if (view.Controls.Any(control => control.Button == null || control.Label == null))
                    throw new InvalidOperationException("Unresolved button: " + screen);
                views.Add(new JObject { ["screen"] = screen, ["path"] = path, ["guid"] = AssetDatabase.AssetPathToGUID(path), ["controls"] = new JArray(view.Controls.Select(c => c.Action)) });
            }
            return new JObject { ["scene"] = ScenePath, ["sceneGuid"] = AssetDatabase.AssetPathToGUID(ScenePath), ["createdAssets"] = new JArray(Created), ["views"] = views };
        }
    }
}
