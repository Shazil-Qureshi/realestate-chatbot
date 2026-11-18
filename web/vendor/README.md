# Third-party files

| File | What | Version | Licence | Get it |
|---|---|---|---|---|
| `lottie_light.min.js` | lottie-web, plays the robot animation | 5.12.2 | MIT | See below |

Downloaded on the project machine on 16 Nov 2026 (168,236 bytes, verified as
lottie-web 5.12.2). To fetch it again, from the project folder in PowerShell:

```powershell
Invoke-WebRequest https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie_light.min.js -OutFile web\vendor\lottie_light.min.js
```

If this file is missing the chat still works; the robot is simply not shown.
