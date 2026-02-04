Create a React Native screen with navigation, layout, and platform-specific handling.

## Steps


1. Define the screen requirements:
2. Set up the screen file:
3. Build the layout:
4. Add data fetching:
5. Add navigation:
6. Test on both iOS and Android simulators.
7. Handle keyboard avoidance for forms.

## Format


```
Screen: <name>
Navigator: <stack|tab|drawer>
Data: <API endpoints or data sources>
Platform Handling: <iOS/Android differences>
```


## Rules

- Always use SafeAreaView for screens that touch screen edges.
- Handle both iOS and Android keyboard behavior.
- Use FlatList over ScrollView for long lists (performance).

