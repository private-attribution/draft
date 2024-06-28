export function JSONSafeParse(s: string) {
  try {
    return JSON.parse(s);
  } catch (error) {
    if (error instanceof SyntaxError) {
      console.error(`${error}`);
      console.error(`Failed to parse JSON from string ${s}`);
      return {};
    }
    throw error;
  }
}
