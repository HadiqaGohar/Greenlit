const PREFIX = "greenlit-script:";

export function saveScriptForReport(reportId: string, scriptText: string): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(`${PREFIX}${reportId}`, scriptText);
}

export function getScriptForReport(reportId: string): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(`${PREFIX}${reportId}`);
}
