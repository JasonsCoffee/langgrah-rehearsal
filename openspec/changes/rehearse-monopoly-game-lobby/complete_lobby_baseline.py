"""Finish approved configuration data and entry context before contract freeze."""
from pathlib import Path
import os
import re
import subprocess
from uuid import NAMESPACE_URL, uuid5

module = Path(os.environ['LOBBY_RUN_ROOT']).resolve() / 'module'
host = Path(os.environ['UNITY_HOST']).resolve()
if Path(subprocess.check_output(['git','-C',str(module),'rev-parse','--show-toplevel'],text=True).strip()).resolve() != module:
    raise ValueError('Independent module required')
game = host / 'Assets/JJGame/monopoly'
path = module / 'Runtime/Script/UI/LobbyRehearsal/LobbyConfiguration.cs'
text = path.read_text(encoding='utf-8')
marker = '        public List<LobbyCatalogDefinition> Catalog'
if 'RechargeIngots' not in text:
    text = text.replace(marker, '''        public List<int> RechargePricesCents = new List<int> { 300, 2000, 5000, 10000, 20000, 50000 };
        public List<int> RechargeIngots = new List<int> { 30, 200, 500, 1000, 2000, 5000 };
        public List<long> ExchangeCoins = new List<long> { 3000, 20000, 50000, 100000, 200000, 500000 };
        public List<long> VipThresholdCents = new List<long> { 1, 3000, 10000, 30000, 100000, 200000, 500000 };
        public List<string> CardIds = new List<string> { "monthly", "golden-annual", "diamond-annual" };
        public List<int> CardPricesCents = new List<int> { 3000, 29800, 99800 };
        public List<long> CardInitialCoins = new List<long> { 15000, 180000, 500000 };
        public List<long> CardPeriodicCoins = new List<long> { 1500, 1500, 20000 };
        public List<int> CardPeriodDays = new List<int> { 1, 1, 7 };
''' + marker)
    path.write_bytes(text.encode())
# Only the approved existing entry is eligible for implementation. Context copies
# stay protected; the host's original files remain untouched by this operation.
for relative in ('Runtime/Script/Monopoly.cs','Runtime/Script/Monopoly.cs.meta',
                 'Runtime/Script/MonopolyRootScene.cs','AGENTS.md',
                 'Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef',
                 'Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef.meta'):
    target = module / relative
    data = (game / relative).read_bytes()
    if target.exists() and target.read_bytes() != data:
        raise ValueError('Existing baseline differs: ' + relative)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
relative = 'Editor/Script/LobbyRehearsal/LobbyRehearsalPanel.cs'
target = module / relative
if not target.exists():
    target.write_bytes(b'// Nonfunctional review-panel shell. Implementation belongs to SHELL.\nusing UnityEditor;\nnamespace jj.Reserve04.Editor.LobbyRehearsal\n{\n    public sealed class LobbyRehearsalPanel : EditorWindow\n    {\n    }\n}\n')
    guid = uuid5(NAMESPACE_URL,'monopoly-game-lobby/api/'+relative).hex
    Path(str(target)+'.meta').write_text('fileFormatVersion: 2\nguid: '+guid+'\n',encoding='utf-8')
# Disconnect cross-font weights on the private copied static font. This prevents
# the placeholder presentation from persisting changes in shared font assets.
font = module / 'Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/Art/LobbyFont_placeHolder.asset'
data = font.read_bytes()
data = re.sub(rb'(regularTypeface|italicTypeface): \{fileID: -?\d+, guid: [0-9a-f]+, type: \d+\}',
              rb'\1: {fileID: 0}',data)
font.write_bytes(data)
print('Prepared approved configuration, entry context, isolated font and panel shell')
