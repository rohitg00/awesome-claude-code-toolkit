Create a Flutter platform channel for native iOS and Android communication.

## Steps


1. Define the platform channel interface:
2. Create the Dart side:
3. Implement the iOS handler (Swift):
4. Implement the Android handler (Kotlin):
5. Add EventChannel if streaming data is needed:
6. Test communication on both platforms.
7. Handle edge cases (app backgrounding, channel not available).

## Format


```
Channel: <channel name>
Methods:
  - <method>(<params>) -> <return type>
Events:
```


## Rules

- Use consistent channel names across Dart, iOS, and Android.
- Always handle PlatformException on the Dart side.
- Return structured data as Maps, not raw strings.

