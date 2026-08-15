import React, { useEffect, useState } from "react";
import type { PlatformPrompt } from "@supremeai/shared-services";

/**
 * Desktop-এ PlatformPrompt-এর React implementation।
 * window.prompt/confirm এর বদলে modal ডায়ালগ দেখায়।
 *
 * JIT OTP-র জন্য shared-services-এর `promptForOtp()` দুটি showInputBox কল করে
 * (reason, তারপর OTP code) — এই queue sequential modal চালায়।
 */

interface PendingInput {
  options: {
    title?: string;
    prompt?: string;
    placeHolder?: string;
    password?: boolean;
    validateInput?: (value: string) => string | null | undefined;
  };
  resolve: (value: string | undefined) => void;
}

interface PendingConfirm {
  message: string;
  resolve: (value: boolean) => void;
}

export type PendingState =
  | { kind: "input"; data: PendingInput }
  | { kind: "confirm"; data: PendingConfirm }
  | null;

class DialogQueue implements PlatformPrompt {
  private listener: ((pending: PendingState) => void) | null = null;
  private pendingInput: PendingInput | null = null;
  private pendingConfirm: PendingConfirm | null = null;

  setListener(fn: (pending: PendingState) => void): void {
    this.listener = fn;
    this.notify();
  }

  private notify(): void {
    if (!this.listener) return;
    if (this.pendingInput) {
      this.listener({ kind: "input", data: this.pendingInput });
    } else if (this.pendingConfirm) {
      this.listener({ kind: "confirm", data: this.pendingConfirm });
    } else {
      this.listener(null);
    }
  }

  async showInputBox(options: PendingInput["options"]): Promise<string | undefined> {
    return new Promise<string | undefined>((resolve) => {
      this.pendingInput = { options, resolve };
      this.notify();
    });
  }

  async showConfirm(message: string): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      this.pendingConfirm = { message, resolve };
      this.notify();
    });
  }

  async withProgress(_title: string, task: () => Promise<void>): Promise<void> {
    await task();
  }

  submit(value: string): void {
    const input = this.pendingInput;
    this.pendingInput = null;
    this.notify();
    input?.resolve(value);
  }

  cancel(): void {
    const input = this.pendingInput;
    const confirm = this.pendingConfirm;
    this.pendingInput = null;
    this.pendingConfirm = null;
    this.notify();
    input?.resolve(undefined);
    confirm?.resolve(false);
  }

  confirmWith(yes: boolean): void {
    const confirm = this.pendingConfirm;
    this.pendingConfirm = null;
    this.notify();
    confirm?.resolve(yes);
  }
}

/** মডিউল-লেভেল singleton — পুরো app এই একটাই prompt ব্যবহার করে। */
export const desktopPrompt: PlatformPrompt & {
  setListener(fn: (pending: PendingState) => void): void;
  submit(value: string): void;
  cancel(): void;
  confirmWith(yes: boolean): void;
} = new DialogQueue();
// ------------------------------------------------------------------
// React Host কম্পোনেন্ট — অ্যাপের যেকোনো জায়গায় mount করা যায়
// ------------------------------------------------------------------

export const JitOtpDialogHost: React.FC = () => {
  const [pending, setPending] = useState<PendingState>(null);
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    desktopPrompt.setListener((p) => {
      setPending(p);
      setValue("");
      setError(null);
    });
    return () => desktopPrompt.setListener(() => null);
  }, []);

  if (!pending) return null;

  const resolveOk = () => {
    if (pending.kind === "input") {
      const validate = pending.data.options.validateInput;
      if (validate) {
        const err = validate(value);
        if (err) {
          setError(err);
          return;
        }
      }
      desktopPrompt.submit(value);
    } else {
      desktopPrompt.confirmWith(true);
    }
  };

  const data = pending.kind === "input" ? pending.data.options : null;

  return (
    <div className="fixed inset-0 z-[9999] bg-black/70 flex items-center justify-center">
      <div className="bg-[#1e1e1e] border border-gray-700 rounded-xl shadow-2xl w-[420px] p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="text-blue-400 font-bold text-sm">{data?.title || "SupremeAI"}</div>
          <button
            className="text-gray-400 hover:text-white"
            onClick={() =>
              pending.kind === "input"
                ? desktopPrompt.cancel()
                : desktopPrompt.confirmWith(false)
            }
            aria-label="Cancel"
          >
            ✕
          </button>
        </div>

        {pending.kind === "confirm" ? (
          <>
            <p className="text-gray-300 text-sm mb-4 whitespace-pre-wrap">{pending.data.message}</p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => desktopPrompt.confirmWith(false)}
                className="px-4 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs font-semibold"
              >
                No
              </button>
              <button
                onClick={() => desktopPrompt.confirmWith(true)}
                className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
              >
                Yes
              </button>
            </div>
          </>
        ) : data ? (
          <>
            <p className="text-gray-300 text-sm mb-1">{data.prompt}</p>
            <input
              autoFocus
              type={data.password ? "password" : "text"}
              value={value}
              placeholder={data.placeHolder}
              onChange={(e) => {
                setValue(e.target.value);
                setError(null);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") resolveOk();
              }}
              className="w-full bg-[#0d1117] border border-gray-600 rounded px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-blue-500"
            />
            {error && <p className="text-red-400 text-xs mt-1.5">{error}</p>}
            <div className="flex justify-end mt-4 space-x-2">
              <button
                onClick={() => desktopPrompt.cancel()}
                className="px-4 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={resolveOk}
                className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
              >
                Submit
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};