"""Architect preparation of binding-only shells in the independent module."""

import os
from pathlib import Path
import subprocess
from uuid import NAMESPACE_URL, uuid5


module = Path(os.environ["LOBBY_RUN_ROOT"]).resolve() / "module"
actual = subprocess.check_output(["git", "-C", str(module), "rev-parse", "--show-toplevel"], text=True).strip()
if Path(actual).resolve() != module:
    raise ValueError("Preparation requires the independent module repository")
ui = "Runtime/Script/UI/LobbyRehearsal/"


def write(relative: str, content: str) -> None:
    path = module / relative
    data = content.encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Prepared shell already differs: " + relative)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    if relative.endswith(".cs"):
        guid = uuid5(NAMESPACE_URL, "monopoly-game-lobby/preparation/" + relative).hex
        write(relative + ".meta", "fileFormatVersion: 2\nguid: " + guid + "\nMonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")


screens = ("Lobby", "Appearance", "Friends", "Shop", "Records", "Chat", "Recharge", "Settings", "Handoff", "PlatformHome")
write(ui + "LobbyStreetBinding.cs", """// Architect-prepared serialized scene references.
using System.Collections.Generic;
using UnityEngine;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public sealed class LobbyStreetBinding : MonoBehaviour
    {
        public Camera WorldCamera;
        public Transform CharacterMount;
        public Transform VehicleMount;
        public Animator CharacterAnimator;
        public List<GameObject> SkinPrefabs = new List<GameObject>();
        public List<GameObject> VehiclePrefabs = new List<GameObject>();
        public LobbyConfiguration Configuration;
    }
}
""")
write(ui + "LobbyConfiguration.cs", """// Architect-prepared approved rehearsal data.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    [Serializable]
    public sealed class LobbyCatalogDefinition
    {
        public string Id;
        public string Name;
        public string Kind;
        public string Gender;
        public int UnlockType;
        public int ShopPriority;
        public int Price;
        public int DurationDays;
        public GameObject Prefab;
        public Sprite Thumbnail;
    }

    public sealed class LobbyConfiguration : ScriptableObject
    {
        public List<int> BaseValues = new List<int> { 10, 50, 250, 1000, 5000 };
        public int EntryFeeMultiplier = 10;
        public long InitialCoins = 10000;
        public long InitialIngots = 200;
        public int FriendLimit = 100;
        public int FriendRequestDays = 7;
        public int PartnerLimit = 20;
        public int RivalLimit = 20;
        public int InvitationSeconds = 30;
        public int MatchHeartbeatSeconds = 3;
        public int MatchTimeoutSeconds = 30;
        public int MatchSeats = 24;
        public int WorldCooldownSeconds = 3;
        public int MessageCharacterLimit = 200;
        public int MonthlyCardDays = 30;
        public int AnnualCardDays = 365;
        public List<LobbyCatalogDefinition> Catalog = new List<LobbyCatalogDefinition>();
    }
}
""")
write(ui + "LobbyRehearsalViewBase.cs", """// Architect-prepared UI references. Business handlers are delegated.
using System;
using System.Collections.Generic;
using jj.WidgetSDK.Runtime;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    [Serializable]
    public sealed class LobbyControlBinding
    {
        public string Action;
        public Button Button;
        public TextMeshProUGUI Label;
    }

    public abstract class LobbyRehearsalViewBase : View
    {
        public TextMeshProUGUI Title;
        public TextMeshProUGUI Status;
        public TMP_InputField Input;
        public ScrollRect Scroll;
        public RectTransform SafeArea;
        public List<LobbyControlBinding> Controls = new List<LobbyControlBinding>();
    }
}
""")
write(ui + "LobbyRehearsalVMBase.cs", """// Architect-prepared lifecycle hooks. Implemented by the SHELL unit.
using jj.WidgetSDK.Runtime;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public abstract partial class LobbyRehearsalVMBase : ViewModel
    {
        public abstract string Screen { get; }

        public override void ViewAppeared()
        {
            base.ViewAppeared();
            AttachLobby();
        }

        public override void ViewDisappeared()
        {
            DetachLobby();
            base.ViewDisappeared();
        }

        public override void Dispose()
        {
            DetachLobby();
            base.Dispose();
        }

        partial void AttachLobby();
        partial void DetachLobby();
    }
}
""")
for screen in screens:
    write(ui + screen + "View.cs", """using jj.WidgetSDK.Runtime;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    [ViewRouter("monopoly/UI/Prefabs/LobbyRehearsal/SCREENView_placeHolder.prefab")]
    public sealed partial class SCREENView : LobbyRehearsalViewBase
    {
    }
}
""".replace("SCREEN", screen))
    write(ui + screen + "Presenter.cs", """using jj.WidgetSDK.Runtime;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    [RequireView("monopoly", typeof(SCREENView))]
    public sealed partial class SCREENPresenter : Presenter, ISystemBackExecutor
    {
        public bool ExecuteBackOperation()
        {
            var handled = false;
            HandleLobbyBack(ref handled);
            return handled;
        }

        partial void HandleLobbyBack(ref bool handled);
    }
}
""".replace("SCREEN", screen))
    write(ui + screen + "VM.cs", """using jj.WidgetSDK.Runtime;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    [ViewPresenter(typeof(SCREENPresenter))]
    public sealed class SCREENVM : LobbyRehearsalVMBase
    {
        public override string Screen => "SCREEN";
    }
}
""".replace("SCREEN", screen))
print("Prepared 34 binding/configuration shells and script metadata")

