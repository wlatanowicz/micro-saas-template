import { useColorScheme } from "react-native";

export type AppTheme = {
  dark: boolean;
  bg: string;
  card: string;
  border: string;
  text: string;
  dimmed: string;
  primary: string;
  dangerBg: string;
  dangerText: string;
  radius: number;
  pad: number;
};

export function useAppTheme(): AppTheme {
  const dark = useColorScheme() === "dark";
  return {
    dark,
    bg: dark ? "#1A1B1E" : "#FFFFFF",
    card: dark ? "#25262B" : "#FFFFFF",
    border: dark ? "#373A40" : "#DEE2E6",
    text: dark ? "#C1C2C5" : "#212529",
    dimmed: dark ? "#909296" : "#868E96",
    primary: "#228BE6",
    dangerBg: dark ? "#4D1F1F" : "#FFF5F5",
    dangerText: dark ? "#FFA8A8" : "#C92A2A",
    radius: 8,
    pad: 16,
  };
}
