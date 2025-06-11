import { useColorScheme } from 'react-native';

const lightColors = {
  background: '#ffffff',
  text: '#000000',
};

const darkColors = {
  background: '#000000',
  text: '#ffffff',
};

export function useThemeColor(
  props: { light?: string; dark?: string },
  colorName: keyof typeof lightColors
) {
  const theme = useColorScheme();
  const colorFromProps = theme === 'dark' ? props.dark : props.light;

  if (colorFromProps) {
    return colorFromProps;
  }

  return theme === 'dark' ? darkColors[colorName] : lightColors[colorName];
}
