import { translateApiError } from "@micro-saas/i18n";
import type { AuthConfig, MeUser } from "@micro-saas/api-client";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { api } from "../api";
import { AppButton, Field } from "../ui";
import { useAppTheme } from "../theme";

type SignInFormProps = {
  authConfig: AuthConfig;
  busy: boolean;
  onBusyChange: (busy: boolean) => void;
  onError: (message: string | null) => void;
  onSuccess: (user: MeUser, token: string) => void;
  onCreateAccount: () => void;
  onForgotPassword: () => void;
};

export function SignInForm({
  authConfig,
  busy,
  onBusyChange,
  onError,
  onSuccess,
  onCreateAccount,
  onForgotPassword,
}: SignInFormProps) {
  const { t } = useTranslation();
  const theme = useAppTheme();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignIn = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await api.signInRequest(email, password);
      if (!result.ok) {
        onError(translateApiError(t, result.errorCode, result.errorParams));
        return;
      }
      onSuccess(result.data.user, result.data.access_token);
    } catch (e) {
      onError(e instanceof Error ? e.message : t("errors.requestFailed"));
    } finally {
      onBusyChange(false);
    }
  };

  return (
    <View style={{ gap: 8 }}>
      <Field
        label={t("auth.email")}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        editable={!busy}
      />
      <Field
        label={t("auth.password")}
        autoComplete="password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        editable={!busy}
      />
      <AppButton label={t("auth.signIn")} onPress={() => void handleSignIn()} loading={busy} />
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 16, marginTop: 8 }}>
        <Pressable onPress={onCreateAccount}>
          <Text style={{ color: theme.primary }}>{t("auth.createAccount")}</Text>
        </Pressable>
        {authConfig.password ? (
          <Pressable onPress={onForgotPassword}>
            <Text style={{ color: theme.primary }}>{t("auth.forgotPassword")}</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}
