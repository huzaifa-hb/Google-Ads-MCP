export type ParsedArgs = {
  command: string;
  subcommand?: string;
  flags: Record<string, string | boolean>;
  positionals: string[];
};

export function parseArgs(argv: string[]): ParsedArgs {
  const [command = "help", maybeSubcommand, ...rest] = argv;
  const hasSubcommand = command === "cloud" && maybeSubcommand && !maybeSubcommand.startsWith("-");
  const tokens = hasSubcommand ? rest : argv.slice(1);
  const flags: Record<string, string | boolean> = {};
  const positionals: string[] = [];

  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (!token) {
      continue;
    }
    if (!token.startsWith("--")) {
      positionals.push(token);
      continue;
    }
    const withoutPrefix = token.slice(2);
    const eqIndex = withoutPrefix.indexOf("=");
    if (eqIndex >= 0) {
      flags[withoutPrefix.slice(0, eqIndex)] = withoutPrefix.slice(eqIndex + 1);
      continue;
    }
    const next = tokens[i + 1];
    if (next && !next.startsWith("--")) {
      flags[withoutPrefix] = next;
      i += 1;
    } else {
      flags[withoutPrefix] = true;
    }
  }

  return {
    command,
    subcommand: hasSubcommand ? maybeSubcommand : undefined,
    flags,
    positionals
  };
}

export function flagString(
  flags: Record<string, string | boolean>,
  name: string,
  fallback?: string
): string | undefined {
  const value = flags[name];
  if (typeof value === "string") {
    return value;
  }
  return fallback;
}

export function flagBool(flags: Record<string, string | boolean>, name: string): boolean {
  return flags[name] === true || flags[name] === "true" || flags[name] === "1";
}
