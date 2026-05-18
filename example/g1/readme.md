This example is a test of Unitree G1/H1-2 robot.

**Note:** 
idl/unitree_go is used for Unitree Go2/B2/H1/B2w/Go2w robots
idl/unitree_hg is used for Unitree G1/H1-2 robots

## Voice text action classifier

`high_level/g1_voice_text_action_classifier.py` maps recognized voice text to a
high-level G1 action. It runs in dry-run mode by default:

```bash
python3 high_level/g1_voice_text_action_classifier.py "请向前走"
python3 high_level/g1_voice_text_action_classifier.py "请和我握手"
```

To execute on a real G1, keep the area clear and pass the robot network
interface:

```bash
python3 high_level/g1_voice_text_action_classifier.py --execute --iface eth0
```
