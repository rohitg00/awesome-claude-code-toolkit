# /create-activity - Create Android Activity/Screen

Generate a Jetpack Compose screen with proper architecture.

## Steps

1. Ask the user for the screen name, purpose, and navigation requirements
2. Create the Composable function with the screen content
3. Add a ViewModel class for the screen's state management
4. Define the UI state as an immutable data class with all screen properties
5. Implement the screen layout using Compose components: Column, Row, LazyList
6. Add navigation parameters using Navigation Compose type-safe arguments
7. Include loading, error, and empty state handling with proper UI
8. Add Material 3 theming: colors, typography, shapes from the app theme
9. Implement pull-to-refresh, pagination, or infinite scroll if applicable
10. Add content descriptions for accessibility (TalkBack support)
11. Create a Compose Preview with @Preview annotation and sample data
12. Register the screen in the navigation graph

## Rules

- Follow the UDF (Unidirectional Data Flow) pattern with ViewModel
- Use StateFlow in ViewModel, collected as State in Composable
- Keep Composable functions stateless; hoist state to the caller
- Use remember and derivedStateOf for expensive computations
- Follow Material 3 guidelines for spacing, elevation, and component usage
- Support both portrait and landscape orientations
- Add string resources for all user-visible text (no hardcoded strings)
