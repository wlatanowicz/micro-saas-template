import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

import { useAppTheme, type AppTheme } from "./theme";

type ButtonVariant = "filled" | "default" | "subtle";

export function Card({ children }: { children: ReactNode }) {
  const theme = useAppTheme();
  return (
    <View
      style={{
        borderWidth: 1,
        borderColor: theme.border,
        borderRadius: theme.radius,
        padding: theme.pad,
        backgroundColor: theme.card,
        marginBottom: theme.pad,
      }}
    >
      {children}
    </View>
  );
}

export function AppButton({
  label,
  onPress,
  disabled,
  loading,
  variant = "filled",
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: ButtonVariant;
}) {
  const theme = useAppTheme();
  const palette = buttonPalette(theme, variant);
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.button,
        {
          backgroundColor: palette.bg,
          borderColor: palette.border,
          opacity: disabled || loading ? 0.6 : pressed ? 0.85 : 1,
        },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={palette.fg} />
      ) : (
        <Text style={{ color: palette.fg, fontWeight: "600" }}>{label}</Text>
      )}
    </Pressable>
  );
}

export function Field({
  label,
  ...inputProps
}: { label: string } & TextInputProps) {
  const theme = useAppTheme();
  return (
    <View style={styles.field}>
      <Text style={{ color: theme.text, marginBottom: 6, fontWeight: "500" }}>{label}</Text>
      <TextInput
        {...inputProps}
        placeholderTextColor={theme.dimmed}
        style={[
          styles.input,
          {
            color: theme.text,
            borderColor: theme.border,
            backgroundColor: theme.bg,
          },
          inputProps.style,
        ]}
      />
    </View>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  const theme = useAppTheme();
  return (
    <View
      style={{
        backgroundColor: theme.dangerBg,
        borderRadius: theme.radius,
        padding: 12,
      }}
    >
      <Text style={{ color: theme.dangerText }}>{message}</Text>
    </View>
  );
}

function buttonPalette(theme: AppTheme, variant: ButtonVariant) {
  if (variant === "filled") {
    return { bg: theme.primary, border: theme.primary, fg: "#FFFFFF" };
  }
  if (variant === "subtle") {
    return { bg: "transparent", border: "transparent", fg: theme.primary };
  }
  return { bg: theme.card, border: theme.border, fg: theme.text };
}

const styles = StyleSheet.create({
  button: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 42,
  },
  field: {
    marginBottom: 10,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
});
