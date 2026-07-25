export function toTitleCase(str: string): string {
  if (!str) return "";
  const lowerWords = new Set([
    "de",
    "da",
    "do",
    "dos",
    "das",
    "e",
    "em",
    "por",
    "com",
    "para",
    "a",
    "o",
    "as",
    "os",
  ]);
  return str
    .toLowerCase()
    .split(" ")
    .map((word, index) => {
      if (!word) return "";
      if (index > 0 && lowerWords.has(word)) {
        return word;
      }
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}
