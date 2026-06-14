import { Group, Input, PinInput } from "@mantine/core";

type SixCharCodeInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export function SixCharCodeInput({ label, value, onChange, disabled }: SixCharCodeInputProps) {
  return (
    <Input.Wrapper label={label}>
      <Group justify="center" mt="xs">
        <PinInput
          length={6}
          type="alphanumeric"
          oneTimeCode
          value={value}
          onChange={(next) => {
            onChange(next.toUpperCase());
          }}
          aria-label={label}
          disabled={disabled}
        />
      </Group>
    </Input.Wrapper>
  );
}
