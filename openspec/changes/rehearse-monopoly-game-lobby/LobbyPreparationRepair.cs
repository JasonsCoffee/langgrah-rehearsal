// Architect-only repair of missing serialized placeholder bindings. No game logic.
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
    public sealed class RepairLobbyBindingsCommand : IUnityOpCommand
    {
        public string CommandName => "RepairMonopolyLobbyBindings";
        const string Root = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/";
        public string Execute(string json)
        {
            try
            {
                var report = (string)JObject.Parse(json)["reportPath"];
                if (string.IsNullOrEmpty(report) || File.Exists(report)) throw new InvalidOperationException("Fresh trusted report path required");
                var walletPath = Root + "SharedWallet_placeHolder.prefab";
                if (AssetDatabase.LoadAssetAtPath<GameObject>(walletPath) != null) throw new InvalidOperationException("Repair already prepared; reconcile receipt");
                var lobby = PrefabUtility.LoadPrefabContents(Root + "LobbyView_placeHolder.prefab");
                GameObject wallet = null;
                try
                {
                    wallet = new GameObject("SharedWallet", typeof(RectTransform));
                    Configure(wallet.GetComponent<RectTransform>(), 0, 0, 1080, 120);
                    var view = lobby.GetComponent<LobbyRehearsalViewBase>();
                    foreach (var action in new[] { "Coins", "Ingots", "Primary" })
                    {
                        var existing = view.Controls.Single(c => c.Action == action);
                        var clone = UnityEngine.Object.Instantiate(existing.Button.gameObject, wallet.transform, false);
                        clone.name = action;
                        if (action == "Primary")
                        {
                            Configure(clone.GetComponent<RectTransform>(), 760, 30, 160, 85);
                            clone.GetComponentInChildren<TextMeshProUGUI>(true).text = "+";
                        }
                    }
                    PrefabUtility.SaveAsPrefabAsset(wallet, walletPath);
                }
                finally
                {
                    if (wallet != null) UnityEngine.Object.DestroyImmediate(wallet);
                    PrefabUtility.UnloadPrefabContents(lobby);
                }
                foreach (var screen in new[] { "Lobby", "Recharge" })
                {
                    var path = Root + screen + "View_placeHolder.prefab";
                    var contents = PrefabUtility.LoadPrefabContents(path);
                    try
                    {
                        var view = contents.GetComponent<LobbyRehearsalViewBase>();
                        foreach (var control in view.Controls.Where(c => c.Action == "Coins" || c.Action == "Ingots" || c.Action == "Primary").ToArray())
                        {
                            view.Controls.Remove(control);
                            UnityEngine.Object.DestroyImmediate(control.Button.gameObject);
                        }
                        var instance = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(walletPath), view.SafeArea);
                        foreach (var action in new[] { "Coins", "Ingots", "Primary" })
                        {
                            var button = instance.transform.Find(action).GetComponent<Button>();
                            view.Controls.Add(new LobbyControlBinding { Action=action, Button=button, Label=button.GetComponentInChildren<TextMeshProUGUI>(true) });
                        }
                        view.Title.gameObject.SetActive(false);
                        if (screen == "Lobby")
                        {
                            var outside = Control(view,"Outside",view.SafeArea,0,0,1080,2160,"");
                            outside.transform.SetAsFirstSibling();
                            outside.GetComponent<Image>().color = Color.clear;
                            outside.gameObject.SetActive(false);
                            var marquee = view.Controls.Single(c => c.Action == "Marquee");
                            var badge = Control(view,"MarqueeBadge",marquee.Button.transform,930,0,60,60,"0");
                            badge.interactable = false;
                            badge.GetComponent<Image>().raycastTarget = false;
                        }
                        EditorUtility.SetDirty(view);
                        PrefabUtility.SaveAsPrefabAsset(contents,path);
                    }
                    finally { PrefabUtility.UnloadPrefabContents(contents); }
                }
                var result = new JObject { ["wallet"]=walletPath,["views"]=new JArray("Lobby","Recharge"),["addedActions"]=new JArray("Outside","MarqueeBadge"),["businessLogicWritten"]=false };
                File.WriteAllText(report,result.ToString());
                return CommandResult.SuccessWithData(result.ToString()).ToJson();
            }
            catch (Exception error) { return CommandResult.Error(error.ToString()).ToJson(); }
        }
        static void Configure(RectTransform rect,float x,float y,float width,float height)
        {
            rect.anchorMin=rect.anchorMax=new Vector2(0,1); rect.pivot=new Vector2(0,1);
            rect.anchoredPosition=new Vector2(x,-y); rect.sizeDelta=new Vector2(width,height);
        }
        static Button Control(LobbyRehearsalViewBase view,string action,Transform parent,float x,float y,float width,float height,string caption)
        {
            var node=new GameObject(action,typeof(RectTransform),typeof(Image),typeof(Button));
            node.transform.SetParent(parent,false); Configure(node.GetComponent<RectTransform>(),x,y,width,height);
            var text=new GameObject("Label",typeof(RectTransform),typeof(TextMeshProUGUI));
            text.transform.SetParent(node.transform,false); Configure(text.GetComponent<RectTransform>(),0,0,width,height);
            var label=text.GetComponent<TextMeshProUGUI>(); label.font=view.Title.font; label.text=caption;
            label.fontSize=28; label.raycastTarget=false;
            var button=node.GetComponent<Button>(); button.targetGraphic=node.GetComponent<Image>();
            view.Controls.Add(new LobbyControlBinding { Action=action,Button=button,Label=label });
            return button;
        }
    }
}
