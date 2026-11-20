"""Architect-prepared DTOs, service signatures and nonfunctional baseline stubs."""

import os
import subprocess
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


root = Path(os.environ["LOBBY_RUN_ROOT"]).resolve() / "module"
if Path(subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True).strip()).resolve() != root:
    raise ValueError("API preparation requires the independent module repository")
prefix = "Runtime/Script/UI/LobbyRehearsal/"


def write(name: str, content: str) -> None:
    relative = prefix + name
    path = root / relative
    data = content.encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("API preparation differs from existing source: " + relative)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    guid = uuid5(NAMESPACE_URL, "monopoly-game-lobby/api/" + relative).hex
    (root / (relative + ".meta")).write_bytes(("fileFormatVersion: 2\nguid: " + guid + "\nMonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n").encode())


write("LobbyDtos.cs", """// Architect-prepared shared data contracts.
using System;
using System.Collections.Generic;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public sealed class LobbyResult
    {
        public bool Success;
        public string Message = "";
        public string EntityId = "";
    }

    [Serializable]
    public sealed class LobbyAppearanceGrant
    {
        public string ItemId = "";
        public DateTimeOffset? ExpiresUtc;
    }

    [Serializable]
    public sealed class LobbyCardGrant
    {
        public string CardId = "";
        public DateTimeOffset PurchasedUtc;
        public DateTimeOffset ExpiresUtc;
        public DateTimeOffset NextGrantUtc;
        public HashSet<string> CreditedSlots = new HashSet<string>();
    }

    [Serializable]
    public sealed class LobbyRechargeEvent
    {
        public string OrderId = "";
        public long AmountCents;
        public DateTimeOffset TimeUtc;
    }

    [Serializable]
    public sealed class LobbyAccount
    {
        public string Id = "";
        public string Name = "";
        public string Gender = "any";
        public string Presence = "online";
        public string Game = "monopoly";
        public long Coins;
        public long Ingots;
        public int SelectedTier;
        public string EquippedSkin = "";
        public string EquippedVehicle = "vehicle-none";
        public bool Music = true;
        public bool Effects = true;
        public int QualityTier = -1;
        public List<LobbyAppearanceGrant> Appearances = new List<LobbyAppearanceGrant>();
        public List<LobbyCardGrant> Cards = new List<LobbyCardGrant>();
        public List<LobbyRechargeEvent> RechargeEvents = new List<LobbyRechargeEvent>();
        public HashSet<string> Friends = new HashSet<string>();
        public HashSet<string> ReadMessages = new HashSet<string>();
    }

    [Serializable]
    public sealed class LobbyFriendRequest
    {
        public string Id = "";
        public string Sender = "";
        public string Recipient = "";
        public DateTimeOffset CreatedUtc;
        public string Status = "pending";
    }

    [Serializable]
    public sealed class LobbyInvitation
    {
        public string Id = "";
        public string Sender = "";
        public string Recipient = "";
        public DateTimeOffset ExpiresUtc;
        public string Status = "pending";
    }

    [Serializable]
    public sealed class LobbyParty
    {
        public string Id = "";
        public List<string> Members = new List<string>();
        public int Tier;
        public string QueueId = "";
    }

    [Serializable]
    public sealed class LobbyQueue
    {
        public string Id = "";
        public List<string> Members = new List<string>();
        public int Tier;
        public DateTimeOffset StartedUtc;
        public DateTimeOffset LastHeartbeatUtc;
        public int AvailablePlayers;
        public string Status = "matching";
        public string MatchId = "";
    }

    [Serializable]
    public sealed class LobbySeat
    {
        public string AccountId = "";
        public int Faction;
        public bool IsBot;
        public bool Connected = true;
        public bool AiControlled;
        public bool Abandoned;
        public long GameCoins;
    }

    [Serializable]
    public sealed class LobbyMatchState
    {
        public string Id = "";
        public int Tier;
        public long EntryFee;
        public DateTimeOffset StartedUtc;
        public List<LobbySeat> Seats = new List<LobbySeat>();
        public string Status = "active";
    }

    [Serializable]
    public sealed class LobbyIncome
    {
        public string Id = "";
        public string Source = "rent";
        public long Amount;
        public DateTimeOffset TimeUtc;
    }

    [Serializable]
    public sealed class LobbyMatchRecord
    {
        public string MatchId = "";
        public string AccountId = "";
        public string Mode = "大赢家";
        public int Tier;
        public int Rank;
        public long EntryFee;
        public long EndingCash;
        public long TotalIncome;
        public long TotalExpenses;
        public long Profit;
        public bool Abandoned;
        public DateTimeOffset EnteredUtc;
        public List<LobbyIncome> Income = new List<LobbyIncome>();
        public List<string> Partners = new List<string>();
        public List<string> TopOpponents = new List<string>();
    }

    public sealed class LobbyRankRow
    {
        public string AccountId = "";
        public string Name = "";
        public int Rank;
        public long Amount;
        public DateTimeOffset AchievedUtc;
    }

    public sealed class LobbyRankingSnapshot
    {
        public DateTimeOffset TimeUtc;
        public List<LobbyRankRow> Day = new List<LobbyRankRow>();
        public List<LobbyRankRow> Week = new List<LobbyRankRow>();
        public LobbyRankRow DaySelf = new LobbyRankRow();
        public LobbyRankRow WeekSelf = new LobbyRankRow();
    }

    [Serializable]
    public sealed class LobbyMessage
    {
        public string Id = "";
        public string Sender = "";
        public string Recipient = "";
        public string Text = "";
        public DateTimeOffset TimeUtc;
    }

    [Serializable]
    public sealed class LobbyReport
    {
        public string Id = "";
        public string Reporter = "";
        public string MessageId = "";
        public DateTimeOffset TimeUtc;
    }

    public sealed class LobbyUnread
    {
        public int World;
        public int Private;
        public int Requests;
        public Dictionary<string, int> Conversations = new Dictionary<string, int>();
    }

    public sealed class LobbyRecommendation
    {
        public string AccountId = "";
        public string Origin = "";
        public DateTimeOffset TimeUtc;
    }

    public sealed class LobbyVip
    {
        public int Level;
        public long SixMonthRechargeCents;
        public long NextThresholdCents;
        public List<string> Benefits = new List<string>();
    }

    [Serializable]
    public sealed class LobbyState
    {
        public int FormatVersion = 1;
        public DateTimeOffset NowUtc = new DateTimeOffset(2026, 11, 18, 0, 0, 0, TimeSpan.Zero);
        public Dictionary<string, LobbyAccount> Accounts = new Dictionary<string, LobbyAccount>();
        public List<LobbyFriendRequest> Requests = new List<LobbyFriendRequest>();
        public List<LobbyInvitation> Invitations = new List<LobbyInvitation>();
        public List<LobbyParty> Parties = new List<LobbyParty>();
        public List<LobbyQueue> Queues = new List<LobbyQueue>();
        public List<LobbyMatchState> Matches = new List<LobbyMatchState>();
        public List<LobbyMatchRecord> Records = new List<LobbyMatchRecord>();
        public List<LobbyMessage> Messages = new List<LobbyMessage>();
        public List<LobbyReport> Reports = new List<LobbyReport>();
        public Dictionary<string, LobbyResult> Operations = new Dictionary<string, LobbyResult>();
        public Dictionary<string, DateTimeOffset> WorldSendTimes = new Dictionary<string, DateTimeOffset>();
    }
}
""")

groups = {
    "LobbyEconomy": [
        ("void", "Initialize", ""),
        ("void", "Save", ""),
        ("LobbyAccount", "Account", "string accountId"),
        ("LobbyAccount", "EnsureAccount", "string accountId, string name, string gender"),
        ("string", "FormatBalance", "long amount"),
        ("LobbyResult", "AdvanceTime", "double seconds"),
        ("long", "EntryFee", "int tier"),
        ("List<LobbyCatalogDefinition>", "ShopItems", "string accountId, string kind"),
        ("List<LobbyCatalogDefinition>", "AppearanceItems", "string accountId, string kind"),
        ("bool", "Owns", "string accountId, string itemId"),
        ("string", "RemainingTime", "string accountId, string itemId"),
        ("LobbyResult", "Equip", "string accountId, string itemId"),
        ("LobbyResult", "BuyItem", "string accountId, string itemId, string operationId"),
        ("LobbyResult", "Exchange", "string accountId, int tier, string operationId"),
        ("LobbyResult", "PurchaseIngots", "string accountId, int tier, string outcome, string operationId"),
        ("LobbyResult", "PurchaseAndExchange", "string accountId, int tier, string paymentOutcome, string exchangeOutcome, string operationId"),
        ("LobbyResult", "PurchaseCard", "string accountId, string cardId, string outcome, string operationId"),
        ("LobbyVip", "Vip", "string accountId"),
    ],
    "LobbyMatch": [
        ("LobbyParty", "Party", "string accountId"),
        ("LobbyQueue", "Queue", "string accountId"),
        ("LobbyMatchState", "Current", "string accountId"),
        ("LobbyResult", "Invite", "string sender, string recipient, string operationId"),
        ("LobbyResult", "Accept", "string invitationId, string recipient"),
        ("LobbyResult", "Reject", "string invitationId, string recipient"),
        ("LobbyResult", "LeaveParty", "string accountId"),
        ("LobbyResult", "SelectTier", "string accountId, int tier"),
        ("LobbyResult", "StartQueue", "string accountId, string operationId"),
        ("LobbyResult", "CancelQueue", "string accountId"),
        ("LobbyResult", "SetAvailablePlayers", "string accountId, int count"),
        ("void", "Tick", ""),
        ("LobbyResult", "SetConnected", "string matchId, string accountId, bool connected"),
        ("LobbyResult", "Reconnect", "string matchId, string accountId"),
        ("LobbyResult", "JoinStarted", "string matchId, string accountId"),
        ("LobbyResult", "Abandon", "string matchId, string accountId, bool confirmed"),
        ("LobbyResult", "Complete", "string matchId, string accountId, string operationId"),
    ],
    "LobbySocial": [
        ("List<LobbyAccount>", "Friends", "string accountId, int page, int pageSize"),
        ("LobbyResult", "RequestFriend", "string sender, string recipient, string operationId"),
        ("LobbyResult", "Respond", "string requestId, string accountId, bool accept"),
        ("LobbyResult", "RemoveFriend", "string accountId, string friendId, bool confirmed"),
        ("List<LobbyFriendRequest>", "Requests", "string accountId"),
        ("void", "Tick", ""),
        ("LobbyResult", "SendWorld", "string accountId, string text, string operationId"),
        ("LobbyResult", "SendPrivate", "string sender, string recipient, string text, string operationId"),
        ("List<LobbyMessage>", "WorldMessages", ""),
        ("List<LobbyMessage>", "PrivateMessages", "string accountId, string peerId"),
        ("List<LobbyAccount>", "Conversations", "string accountId"),
        ("LobbyUnread", "Unread", "string accountId"),
        ("void", "ReadWorld", "string accountId, bool visible"),
        ("void", "ReadPrivate", "string accountId, string peerId"),
        ("void", "SetPrivateVisible", "string accountId, string peerId, bool visible"),
        ("LobbyMessage", "Marquee", ""),
        ("LobbyResult", "Report", "string accountId, string messageId, bool confirmed, string operationId"),
    ],
    "LobbyRecordsSettings": [
        ("LobbyResult", "Publish", "LobbyMatchRecord record, string operationId"),
        ("LobbyRankingSnapshot", "Rankings", "string accountId"),
        ("List<LobbyMatchRecord>", "History", "string accountId, int page, int pageSize"),
        ("List<LobbyRecommendation>", "Recommendations", "string accountId"),
        ("LobbyResult", "SetAudio", "string accountId, bool music, bool effects"),
        ("LobbyResult", "SetQuality", "string accountId, bool high, int lowestTier, int highestTier"),
        ("int", "EffectiveQuality", "string accountId, int deviceTier, int lowestTier, int highestTier"),
        ("string", "Rules", ""),
        ("string", "About", "string version"),
        ("string", "Support", ""),
    ],
}

ports = """// Architect-prepared storage boundary and service signatures.
using System;
using System.Collections.Generic;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public interface ILobbyPersistence
    {
        string Read(string key);
        void Write(string key, string value);
        void Flush();
    }
"""
for name, methods in groups.items():
    ports += "\n    public interface I" + name + "\n    {\n"
    for returns, method, parameters in methods:
        ports += "        " + returns + " " + method + "(" + parameters + ");\n"
    ports += "    }\n"
ports += "}\n"
write("LobbyPorts.cs", ports)

world = """// Architect-prepared dependency composition. Domain behavior is delegated.
using System;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public sealed class LobbyWorld
    {
        public readonly object Sync = new object();
        public readonly LobbyConfiguration Configuration;
        public readonly ILobbyPersistence Persistence;
        public LobbyState State = new LobbyState();
"""
for name in groups:
    world += "        public readonly " + name + " " + name.removeprefix("Lobby") + ";\n"
world += """
        public LobbyWorld(LobbyConfiguration configuration, ILobbyPersistence persistence)
        {
            Configuration = configuration ?? throw new ArgumentNullException(nameof(configuration));
            Persistence = persistence ?? throw new ArgumentNullException(nameof(persistence));
"""
for name in groups:
    world += "            " + name.removeprefix("Lobby") + " = new " + name + "(this);\n"
world += """            Economy.Initialize();
        }
    }
}
"""
write("LobbyWorld.cs", world)

for name, methods in groups.items():
    content = "// Compilable nonfunctional baseline. This file belongs to its delegated unit.\n"
    content += "using System;\nusing System.Collections.Generic;\n\nnamespace jj.Reserve04.Runtime.LobbyRehearsal\n{\n"
    content += "    public sealed class " + name + " : I" + name + "\n    {\n"
    content += "        private readonly LobbyWorld world;\n\n"
    content += "        public " + name + "(LobbyWorld world)\n        {\n            this.world = world;\n        }\n"
    for returns, method, parameters in methods:
        content += "\n        public " + returns + " " + method + "(" + parameters + ")\n        {\n"
        if returns not in ("void",):
            expression = {"bool": "false", "int": "0", "long": "0", "string": '""'}.get(returns, "new " + returns + "()")
            content += "            return " + expression + ";\n"
        content += "        }\n"
    content += "    }\n}\n"
    write(name + ".cs", content)
print("Prepared frozen shared API candidates and four nonfunctional domain stubs")

write("LobbyUiPort.cs", """// Architect-prepared client/framework boundary.
using Cysharp.Threading.Tasks;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public interface ILobbyUiPort
    {
        UniTask NavigateAsync(string screen, LobbyShellBindings context);
        UniTask BackAsync();
        void Notify(string message);
        void Copy(string value);
        string Paste();
        void ApplyAudio(bool music, bool effects);
        void ApplyQuality(int tier);
        string Version { get; }
        int DeviceQualityTier { get; }
        int LowestQualityTier { get; }
        int HighestQualityTier { get; }
    }
}
""")
write("LobbyShellBindings.cs", """// Nonfunctional UI coordinator baseline. Owned by the SHELL implementation unit.
using Cysharp.Threading.Tasks;

namespace jj.Reserve04.Runtime.LobbyRehearsal
{
    public sealed partial class LobbyShellBindings
    {
        private readonly LobbyWorld world;
        private readonly ILobbyUiPort ui;
        public string AccountId { get; private set; } = "";
        public string Screen { get; private set; } = "";
        public string SelectedItemId { get; private set; } = "";
        public string SelectedPeerId { get; private set; } = "";
        public string Tab { get; private set; } = "";
        public string Draft { get; private set; } = "";
        public int Page { get; private set; }
        public LobbyWorld World => world;

        public LobbyShellBindings(LobbyWorld world, ILobbyUiPort ui)
        {
            this.world = world;
            this.ui = ui;
        }

        public UniTask EnterAsync(string accountId)
        {
            return UniTask.CompletedTask;
        }

        public UniTask OpenAsync(string screen, string target)
        {
            return UniTask.CompletedTask;
        }

        public UniTask BackAsync()
        {
            return UniTask.CompletedTask;
        }

        public UniTask ExitAsync()
        {
            return UniTask.CompletedTask;
        }

        public UniTask CommandAsync(string action, string value)
        {
            return UniTask.CompletedTask;
        }

        public void Attach(LobbyRehearsalVMBase viewModel)
        {
        }

        public void Detach(LobbyRehearsalVMBase viewModel)
        {
        }

        public void Refresh()
        {
        }
    }
}
""")
write("Monopoly.LobbyRehearsal.cs", """// Existing-entry lifecycle extension shell. Owned by SHELL.
namespace jj.Reserve04.Runtime
{
    public partial class Monopoly
    {
    }
}
""")
