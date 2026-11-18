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
    // Architect-only synthetic delivery rehearsal. No command is exposed to coders.
    public sealed class FrameworkArtReplacement : IUnityOpCommand
    {
        public string CommandName => "FrameworkArtReplacement";
        const string Art="Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Images/FrameworkVisualDemo/expedition_placeHolder.png";
        const string Prefab="Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab";
        const string Original="94bdc81eb37c682c818e8d5b1cdfca546532c3b48faf2a9aa8d169ba2df54782";
        const string Output=".agent/art-replacement";

        public string Execute(string json)
        {
            try
            {
                if(EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
                    throw new InvalidOperationException("Art preparation requires idle Edit Mode");
                string operation=(string)JObject.Parse(json)["operation"];
                if(operation=="prepare") Prepare();
                else if(operation=="prepare-lake") Prepare(true);
                else if(operation=="lake") return CommandResult.SuccessWithData(Check(true,"compatible-lake").ToString()).ToJson();
                else if(operation=="incompatible") return CommandResult.SuccessWithData(Check(false).ToString()).ToJson();
                else if(operation=="compatible") return CommandResult.SuccessWithData(Check(true).ToString()).ToJson();
                else throw new ArgumentException("Expected prepare, incompatible or compatible");
                return CommandResult.SuccessWithData(new JObject { ["prepared"]=true }.ToString()).ToJson();
            }
            catch(Exception error){return CommandResult.Error(error.Message).ToJson();}
        }

        static void Prepare(bool lake=false)
        {
            string expected=lake?(string)JObject.Parse(File.ReadAllText(Output+"/compatible/result.json"))["after_sha256"]:Original;
            if(Hash(Art)!=expected)throw new InvalidOperationException("Unexpected source artwork");
            foreach(string kind in lake?new[]{"compatible-lake"}:new[]{"compatible","incompatible"})
            {
                string directory=Output+"/"+kind;
                Directory.CreateDirectory(directory);
                string path=directory+"/delivery.png";
                if(File.Exists(path))throw new InvalidOperationException("Delivery exists; preserve its identity");
                int width=kind=="incompatible"?320:768;
                int height=kind=="incompatible"?320:480;
                var texture=new Texture2D(width,height,TextureFormat.RGB24,false);
                try
                {
                    // Code-native geometric fixture: dawn sky, layered ridges, warm sun.
                    for(int y=0;y<height;y++)for(int x=0;x<width;x++)
                    {
                        float u=x/(float)width,v=y/(float)height;
                        Color color=Color.Lerp(new Color32(231,166,143,255),new Color32(60,58,105,255),v);
                        if((u-.73f)*(u-.73f)+(v-.74f)*(v-.74f)*.39f<.008f)color=new Color32(255,226,174,255);
                        if(v<.72f-Math.Abs(u-.31f)*1.1f)color=new Color32(152,142,174,255);
                        if(v<.60f-Math.Abs(u-.64f)*.85f)color=new Color32(94,101,139,255);
                        if(v<.40f-Math.Abs(u-.22f)*.44f)color=new Color32(54,76,111,255);
                        if(v<.25f-Math.Abs(u-.75f)*.23f)color=new Color32(26,53,78,255);
                        if(lake && v<.24f && u>.05f+v*.85f && u<.98f-v*.45f)
                        {
                            color=Color.Lerp(new Color32(48,112,143,255),new Color32(130,166,178,255),v/.24f);
                            if(Math.Abs(u-.73f)<(.025f+(.24f-v)*.20f) && ((int)(v*480)/4)%3==0)
                                color=new Color32(233,203,156,255);
                            else if(((int)(v*480))%19==0 && u>.2f && u<.85f)
                                color=Color.Lerp(color,new Color32(171,198,201,255),.45f);
                        }
                        texture.SetPixel(x,y,color);
                    }
                    texture.Apply();File.WriteAllBytes(path,texture.EncodeToPNG());
                }
                finally{UnityEngine.Object.DestroyImmediate(texture);}
            }
        }

        static JObject Check(bool apply,string deliveryKind=null)
        {
            string kind=deliveryKind??(apply?"compatible":"incompatible");
            string directory=Output+"/"+kind;
            string resultPath=directory+"/result.json";
            if(File.Exists(resultPath))throw new InvalidOperationException("Replacement receipt already exists; reconcile instead of replaying");
            string expected=deliveryKind==null?Original:(string)JObject.Parse(File.ReadAllText(Output+"/compatible/result.json"))["after_sha256"];
            if(Hash(Art)!=expected)throw new InvalidOperationException("Source artwork changed before replacement");
            string before=Hash(Art),meta=Hash(Art+".meta"),prefab=Hash(Prefab);
            var sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art);
            if(sprite==null)throw new InvalidOperationException("Original sprite is not imported");
            AssetDatabase.TryGetGUIDAndLocalFileIdentifier(sprite,out string guid,out long localId);
            var shell=AssetDatabase.LoadAssetAtPath<GameObject>(Prefab).GetComponent<ExpeditionPreviewShell>();
            if(shell==null || shell.heroImage.sprite!=sprite)throw new InvalidOperationException("Original binding is unresolved");
            var importer=AssetImporter.GetAtPath(Art) as TextureImporter;
            if(importer==null || importer.textureType!=TextureImporterType.Sprite || importer.spriteImportMode!=SpriteImportMode.Single
                || importer.mipmapEnabled || !importer.sRGBTexture || importer.textureCompression!=TextureImporterCompression.Uncompressed
                || importer.spritePixelsPerUnit!=100)throw new InvalidOperationException("Original imports differ from artist contract");
            byte[] bytes=File.ReadAllBytes(directory+"/delivery.png");
            var delivery=new Texture2D(2,2,TextureFormat.RGBA32,false);
            int width,height;bool opaque=true;
            try
            {
                if(!delivery.LoadImage(bytes))throw new InvalidOperationException("Delivery is not a decodable image");
                width=delivery.width;height=delivery.height;
                foreach(var pixel in delivery.GetPixels32())if(pixel.a!=255){opaque=false;break;}
            }
            finally{UnityEngine.Object.DestroyImmediate(delivery);}
            bool compatible=width==768 && height==480 && opaque;
            var result=new JObject { ["change_id"]="art-"+kind+"-1",["separate_change"]=true,["coding_cycle_active"]=false,
                ["delivery_sha256"]=Hash(directory+"/delivery.png"),["width"]=width,["height"]=height,["opaque"]=opaque,
                ["compatible"]=compatible,["applied"]=false,["before_sha256"]=before,["guid"]=guid,["local_id"]=localId.ToString(),
                ["review_decision"]="pending" };
            if(!compatible)
            {
                result["reason"]="Dimensions or opacity violate the artist contract; reject delivery or revise contract separately";
                result["unchanged"]=Hash(Art)==before && Hash(Art+".meta")==meta && Hash(Prefab)==prefab;
                File.WriteAllText(resultPath,result.ToString());return result;
            }
            if(!apply)throw new InvalidOperationException("Incompatible fixture unexpectedly passed");
            File.Copy(Art,directory+"/previous.png",false);
            File.Copy(Art+".meta",directory+"/previous.meta",false);
            // Only replace the image bytes. Never delete or recreate its metadata.
            File.WriteAllBytes(Art,bytes);
            AssetDatabase.ImportAsset(Art,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var imported=AssetDatabase.LoadAssetAtPath<Sprite>(Art);
            AssetDatabase.TryGetGUIDAndLocalFileIdentifier(imported,out string afterGuid,out long afterId);
            var current=AssetDatabase.LoadAssetAtPath<GameObject>(Prefab).GetComponent<ExpeditionPreviewShell>();
            bool preserved=guid==afterGuid && localId==afterId && meta==Hash(Art+".meta") && prefab==Hash(Prefab)
                && current.heroImage.sprite==imported && imported.rect.size==new Vector2(768,480);
            result["applied"]=true;result["references_preserved"]=preserved;
            result["after_sha256"]=Hash(Art);result["metadata_sha256"]=Hash(Art+".meta");result["prefab_sha256"]=Hash(Prefab);
            File.WriteAllText(resultPath,result.ToString());
            if(!preserved)throw new InvalidOperationException("Replacement import changed protected references; retained diagnostic evidence");
            return result;
        }

        static string Hash(string path)
        {
            using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-","").ToLowerInvariant();
        }
    }
}
