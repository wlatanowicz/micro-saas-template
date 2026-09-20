import { TextInput, Text, View } from "react-native";

import { useAppTheme } from "../theme";

type SixCharCodeInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export function SixCharCodeInput({ label, value, onChange, disabled }: SixCharCodeInputProps) {
  const theme = useAppTheme();
  return (
    <View>
      <Text style={{ color: theme.text, marginBottom: 6, fontWeight: "500" }}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        autoCapitalize="characters"
        autoComplete="one-time-code"
        autoCorrect={false}
        maxLength={6}
        value={value}
        editable={!disabled}
        onChangeText={(next) => {
          onChange(next.toUpperCase());
        }}
        placeholderTextColor={theme.dimmed}
        style={{
          borderWidth: 1,
          borderColor: theme.border,
          borderRadius: 8,
          paddingHorizontal: 12,
          paddingVertical: 10,
          fontSize: 20,
          letterSpacing: 8,
          textAlign: "center",
          color: theme.text,
        }}
      />
    </View>
  );
}
