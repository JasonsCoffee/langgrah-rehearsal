// Architect-only serialized placeholder binding preparation. No runtime behavior.
using System;
using System.IO;
using System.Linq;
using jj.Reserve04.Runtime.LobbyRehearsal;
using jj.UnityOperator.Editor;
using Newtonsoft.Json.Linq;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace MonopolyLobbyPreparation
{
    public sealed class PrepareLobbyShopCommand : IUnityOpCommand
    {
        public string CommandName => "PrepareMonopolyLobbyShop";
        public string Execute(string json)
        {
            try
            {
                var report = (string)JObject.Parse(json)["reportPath"];
                if (string.IsNullOrEmpty(report) || File.Exists(report)) throw new InvalidOperationException("Fresh trusted receipt required");
                const string path = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/LobbyView_placeHolder.prefab";
                var root = PrefabUtility.LoadPrefabContents(path);
                try
                {
                    var view = root.GetComponent<LobbyRehearsalViewBase>();
                    if (view.Controls.Any(c => c.Action == "Shop")) throw new InvalidOperationException("Shop binding already exists; reconcile receipt");
                    var template = view.Controls.Single(c => c.Action == "Primary");
                    var clone = UnityEngine.Object.Instantiate(template.Button.gameObject, view.SafeArea, false);
                    clone.name = "Shop";
                    var rect = clone.GetComponent<RectTransform>();
                    rect.anchorMin = rect.anchorMax = new Vector2(0, 1);
                    rect.pivot = new Vector2(0, 1);
                    rect.anchoredPosition = new Vector2(930, -30);
                    rect.sizeDelta = new Vector2(140, 85);
                    var label = clone.GetComponentInChildren<TextMeshProUGUI>(true);
                    label.text = "商城";
                    label.fontSize = 28;
                    var button = clone.GetComponent<Button>();
                    button.onClick.RemoveAllListeners();
                    clone.SetActive(true);
                    view.Controls.Add(new LobbyControlBinding { Action = "Shop", Button = button, Label = label });
                    EditorUtility.SetDirty(view);
                    PrefabUtility.SaveAsPrefabAsset(root, path);
                    var result = new JObject { ["path"] = path, ["action"] = "Shop", ["caption"] = "商城",
                        ["position"] = new JArray(930, -30), ["size"] = new JArray(140, 85),
                        ["controlCount"] = view.Controls.Count, ["businessLogicWritten"] = false };
                    File.WriteAllText(report, result.ToString());
                    return CommandResult.SuccessWithData(result.ToString()).ToJson();
                }
                finally { PrefabUtility.UnloadPrefabContents(root); }
            }
            catch (Exception error) { return CommandResult.Error(error.ToString()).ToJson(); }
        }
    }
}
