# Audio Files

This directory is for the pre-generated ElevenLabs MP3 files used by the handover task (`robot_voice_5.py`).

## Required Files

Generate these using the ElevenLabs API or web interface with the **George** voice (British accent):

| Filename | Narration text |
|----------|---------------|
| `system_ready.mp3` | "JARVIS online. Good evening sir. Dual robotic handover sequence primed." |
| `left_arm_picking.mp3` | "Initiating left arm retrieval sequence." |
| `centering_mass.mp3` | "Centering payload. Mass distribution nominal." |
| `rotating_to_handover.mp3` | "Rotating to handover coordinates. Stand by." |
| `extending_left_arm.mp3` | "Extending left arm to transfer position." |
| `right_arm_receiving.mp3` | "Right arm moving to intercept. Tracking payload." |
| `right_arm_grabbing.mp3` | "Payload secured. Grip confirmed." |
| `left_arm_release.mp3` | "Left arm disengaging. Transfer complete, sir." |
| `drop_zone.mp3` | "Navigating to drop zone. Calculating optimal placement." |
| `dropping_object.mp3` | "Releasing payload. Placement confirmed." |
| `homing_both_arms.mp3` | "Returning both arms to home position." |
| `mission_complete.mp3` | "All objectives completed. Systems nominal, sir." |
| `outro.mp3` | "Handover protocol concluded. Both systems returning to standby." |

## Fallback

If MP3 files are not present, `robot_voice_5.py` falls back automatically to the macOS `say` command with the **Daniel** voice. No configuration change needed.

## Storage Location

By default, `robot_voice_5.py` looks for files at:

```
~/Desktop/JARVIS_Audio/
```

Update the `AUDIO_DIR` constant in `robot_voice_5.py` to change this location.

## Note

The coordinated pickup task (`robot_voice_6.py`) uses macOS **Samantha** TTS only and does not require any MP3 files.
