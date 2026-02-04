---
name: mobile-development
description: Mobile development patterns for React Native and Flutter including navigation, state management, and responsive design
---

# Mobile Development

## React Native Component Structure

```tsx
import { View, Text, FlatList, StyleSheet, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

interface Product {
  id: string;
  name: string;
  price: number;
  image: string;
}

function ProductList({ products }: { products: Product[] }) {
  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={products}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <ProductCard product={item} />}
        contentContainerStyle={styles.list}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        ListEmptyComponent={<EmptyState message="No products found" />}
        initialNumToRender={10}
        maxToRenderPerBatch={10}
        windowSize={5}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  list: {
    padding: 16,
  },
  separator: {
    height: 12,
  },
});
```

Use `FlatList` for scrollable lists (never `ScrollView` with `.map()`). Set `windowSize` and `maxToRenderPerBatch` for large lists.

## React Native Navigation

```tsx
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

type RootStackParams = {
  Tabs: undefined;
  ProductDetail: { productId: string };
  Cart: undefined;
};

const Stack = createNativeStackNavigator<RootStackParams>();
const Tab = createBottomTabNavigator();

function TabNavigator() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false }}>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Tabs" component={TabNavigator} options={{ headerShown: false }} />
        <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
        <Stack.Screen name="Cart" component={CartScreen} options={{ presentation: "modal" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

## Flutter Widget Pattern

```dart
class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback onTap;

  const ProductCard({
    super.key,
    required this.product,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        elevation: 2,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
              child: Image.network(
                product.imageUrl,
                height: 200,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, size: 64),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(product.name, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text("\$${product.price.toStringAsFixed(2)}",
                      style: Theme.of(context).textTheme.bodyLarge),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Responsive Layout

```tsx
import { useWindowDimensions } from "react-native";

function useResponsive() {
  const { width } = useWindowDimensions();
  return {
    isPhone: width < 768,
    isTablet: width >= 768 && width < 1024,
    isDesktop: width >= 1024,
    columns: width < 768 ? 1 : width < 1024 ? 2 : 3,
  };
}

function ProductGrid({ products }: { products: Product[] }) {
  const { columns } = useResponsive();

  return (
    <FlatList
      data={products}
      numColumns={columns}
      key={columns}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <View style={{ flex: 1, maxWidth: `${100 / columns}%`, padding: 8 }}>
          <ProductCard product={item} />
        </View>
      )}
    />
  );
}
```

## Platform-Specific Code

```tsx
import { Platform } from "react-native";

const styles = StyleSheet.create({
  shadow: Platform.select({
    ios: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
    },
    android: {
      elevation: 4,
    },
    default: {},
  }),
});
```

## Anti-Patterns

- Using `ScrollView` with `.map()` for dynamic lists (use `FlatList` or `SectionList`)
- Storing all state in a global store instead of colocating with components
- Not handling safe areas (notch, status bar, home indicator)
- Inline styles on every render (define with `StyleSheet.create`)
- Blocking the JS thread with heavy computation (use `InteractionManager`)
- Ignoring platform-specific UX conventions (iOS back swipe, Android back button)

## Checklist

- [ ] `FlatList` used for all scrollable lists with `keyExtractor`
- [ ] Navigation typed with TypeScript route params
- [ ] Safe area insets handled with `SafeAreaView`
- [ ] Styles defined with `StyleSheet.create` (not inline objects)
- [ ] Responsive layouts adapt to phone, tablet, and desktop
- [ ] Platform-specific styles handled with `Platform.select`
- [ ] Images cached and loaded with error/loading states
- [ ] Heavy computation offloaded from the JS thread
