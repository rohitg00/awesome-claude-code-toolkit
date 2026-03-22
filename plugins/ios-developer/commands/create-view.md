# /create-view - Create SwiftUI View

Generate a SwiftUI view with proper architecture and best practices.

## Steps

1. Ask the user for the view name, purpose, and data requirements
2. Determine the view type: screen (full page), component (reusable), or sheet (modal)
3. Create the SwiftUI view file with the appropriate structure
4. Add @State, @Binding, @ObservedObject, or @EnvironmentObject properties as needed
5. Implement the view body with proper layout: VStack, HStack, ZStack, List, or Grid
6. Add navigation elements: NavigationLink, sheet, alert, or confirmationDialog
7. Include loading, empty, and error states with appropriate UI
8. Add accessibility modifiers: accessibilityLabel, accessibilityHint, accessibilityValue
9. Implement dark mode support with proper color assets
10. Create a PreviewProvider with multiple preview configurations
11. Add the view to the navigation flow in the appropriate coordinator or router
12. Document the view's purpose, parameters, and usage examples

## Rules

- Follow MVVM architecture: views should not contain business logic
- Use @StateObject for owned data, @ObservedObject for injected data
- Keep views small; extract subviews for sections over 30 lines
- Use SF Symbols for icons instead of custom assets when available
- Support Dynamic Type for all text elements
- Add proper keyboard handling for form views
- Use the project's design system colors and typography
