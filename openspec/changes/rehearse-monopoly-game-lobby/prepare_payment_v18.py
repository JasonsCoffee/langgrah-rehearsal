"""Architect declarations only; all payment behavior stays delegated."""
from hashlib import sha256
import json
from pathlib import Path


def prepare(source: Path, current: dict, directory: Path) -> None:
    if current['contract_version'] != 18:
        raise ValueError('Bound to the inspected cycle-seventeen dossier')
    base = 'Runtime/Script/UI/LobbyRehearsal/'
    changed = set()

    def replace(name: str, old: str, new: str) -> None:
        path = source / (base + name)
        raw = path.read_bytes().decode('utf-8')
        newline = '\r\n' if '\r\n' in raw else '\n'
        text = raw.replace('\r\n', '\n')
        if text.count(old) != 1:
            raise ValueError('Unexpected declaration baseline: ' + name)
        path.write_bytes(text.replace(old, new).replace('\n', newline).encode())
        changed.add(base + name)

    replace('LobbyDtos.cs', '    [Serializable]\n    public sealed class LobbyAccount', '''    [Serializable]
    public sealed class LobbyPaymentOrder
    {
        public string GameOrderId = "";
        public string PlatformOrderId = "";
        public string ProductId = "";
        public string AccountId = "";
        public string OperationId = "";
        public long AmountCents;
        public string Status = "pending";
        public bool Delivered;
    }

    public sealed class LobbyPaymentCallback
    {
        public string GameOrderId = "";
        public string PlatformOrderId = "";
        public string ProductId = "";
        public string Status = "paid";
    }

    [Serializable]
    public sealed class LobbyPaymentReconciliation
    {
        public string GameOrderId = "";
        public string PlatformOrderId = "";
        public string ProductId = "";
        public int Attempts;
        public bool Complete;
    }

    [Serializable]
    public sealed class LobbyAccount''')
    replace('LobbyDtos.cs', '        public List<string> Benefits = new List<string>();', '        public List<string> Benefits = new List<string>();\n        public List<string> BenefitKeys = new List<string>();')
    replace('LobbyDtos.cs', '        public int FormatVersion = 1;', '''        public int FormatVersion = 1;
        public List<LobbyPaymentOrder> PaymentOrders = new List<LobbyPaymentOrder>();
        public List<LobbyPaymentReconciliation> PaymentReconciliations = new List<LobbyPaymentReconciliation>();''')
    replace('LobbyWorld.cs', '        public LobbyState State = new LobbyState();', '''        public LobbyState State = new LobbyState();
        public Func<LobbyPaymentOrder, bool> PaymentDeliveryAllowed;
        public Func<string, bool> ExchangeCommitAllowed;
        public Func<string, LobbyVip> PlatformVipSnapshot;''')
    declarations = '''        LobbyPaymentOrder BeginCheckout(string accountId, string productId, string operationId);
        LobbyResult ApplyPaymentCallback(LobbyPaymentCallback callback);
        LobbyResult ReconcilePayments();
'''
    replace('LobbyPorts.cs', '        LobbyVip Vip(string accountId);', declarations + '        LobbyVip Vip(string accountId);')
    replace('LobbyEconomy.cs', '        public LobbyVip Vip(string accountId)', '''        public LobbyPaymentOrder BeginCheckout(string accountId, string productId, string operationId)
        {
            return new LobbyPaymentOrder();
        }

        public LobbyResult ApplyPaymentCallback(LobbyPaymentCallback callback)
        {
            return new LobbyResult();
        }

        public LobbyResult ReconcilePayments()
        {
            return new LobbyResult();
        }

        public LobbyVip Vip(string accountId)''')
    replace('LobbyShellBindings.cs', '        public int Page { get; private set; }', '''        public int Page { get; private set; }
        public string PendingPaymentOrderId { get; private set; } = "";
        public bool PaymentLoading { get; private set; }''')
    replace('LobbyConfiguration.cs', '    public sealed class LobbyConfiguration : ScriptableObject', '''    [Serializable]
    public sealed class LobbyLocalizedText
    {
        public string Key = "";
        public string Text = "";
    }

    [Serializable]
    public sealed class LobbyVipBenefitDefinition
    {
        public string Category = "";
        public string LocalizationKey = "";
        public int MinimumLevel = 1;
    }

    public sealed class LobbyConfiguration : ScriptableObject''')
    entries = [
        ('entry', '入场优惠', '入场优惠介绍：演练入场费保持不变。', 1),
        ('merit', '功勋加成', '功勋加成介绍：大赢家功勋权益展示，演练不额外结算。', 1),
        ('feedback', '回馈赛', '回馈赛介绍：西部街区回馈活动展示，演练不开放赛事。', 1),
        ('birthday', '生日礼包', '生日礼包介绍：大赢家生日祝福展示，演练不发放礼包。', 1),
        ('support', '专属客服', '专属客服介绍：可前往模拟平台客服页查看演练帮助。', 1),
        ('rename', '免费改名', '免费改名介绍：大赢家身份权益展示，演练不提供改名。', 1),
        ('reward', '奖励加成', '奖励加成介绍：VIP6及以上专属展示，演练结算奖励保持不变。', 6),
    ]
    benefits = ',\n'.join('            new LobbyVipBenefitDefinition { Category = '+json.dumps(category, ensure_ascii=False)+', LocalizationKey = "lobby.vip.'+key+'", MinimumLevel = '+str(level)+' }' for key, category, _, level in entries)
    texts = ',\n'.join('            new LobbyLocalizedText { Key = "lobby.vip.'+key+'", Text = '+json.dumps(text, ensure_ascii=False)+' }' for key, _, text, _ in entries)
    replace('LobbyConfiguration.cs', '        public List<LobbyCatalogDefinition> Catalog = new List<LobbyCatalogDefinition>();', '''        public List<LobbyVipBenefitDefinition> VipBenefitCatalog = new List<LobbyVipBenefitDefinition>
        {
'''+benefits+'''
        };
        public List<LobbyLocalizedText> LocalizedText = new List<LobbyLocalizedText>
        {
'''+texts+'''
        };
        public List<LobbyCatalogDefinition> Catalog = new List<LobbyCatalogDefinition>();''')
    guide = 'specs/monopoly-game-lobby/payment-api.v18.md'
    (source / guide).write_bytes((directory / 'payment-api.v18.md').read_bytes())
    for unit in current['units']:
        if unit['id'] in ('TEST-CARDS', 'ECON', 'SHELL'):
            unit['instructions'] += ' Cycle 18 supplies payment-api.v18.md with nonfunctional typed checkout/callback/reconciliation and VIP supplier APIs, plus rehearsal localization data. Read the actual declarations. Implement or test the complete original behavior using these seams; the declaration defaults are behavioral Red, not passing implementations. No real backend and no VIP financial effects. Do not bypass independent review.'
    def ref(path):
        return {'path': path, 'sha256': sha256((source / path).read_bytes()).hexdigest()}
    spec = source / 'specs/monopoly-game-lobby'
    profile = json.loads((source / current['coding_profile_ref']['path']).read_bytes())
    for key in ('rules', 'sources'):
        if key in profile:
            profile[key] = [ref(row['path']) if row['path'] in changed else row for row in profile[key]]
    profile['rules'].append(ref(guide))
    profile['protected_paths'].append(guide)
    (spec / 'coding-profile.v18.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='')
    current['coding_profile_ref'] = ref('specs/monopoly-game-lobby/coding-profile.v18.json')
    presentation = json.loads((source / current['presentation_ref']['path']).read_bytes())
    presentation['files'] = [ref(row['path']) if row['path'] in changed else row for row in presentation['files']]
    (spec / 'presentation.v18.json').write_text(json.dumps(presentation, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='')
    current['presentation_ref'] = ref('specs/monopoly-game-lobby/presentation.v18.json')
