"use client";

import React from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = "" }) => {
  const parseMarkdownToElements = (text: string): React.ReactNode[] => {
    if (!text) return [];

    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];
    let listItems: string[] = [];
    let isOrderedList = false;
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeLanguage = "";

    const flushList = (key: string) => {
      if (listItems.length === 0) return;
      const ListTag = isOrderedList ? "ol" : "ul";
      elements.push(
        <ListTag
          key={key}
          className={`my-2 pl-4 space-y-1 ${
            isOrderedList ? "list-decimal" : "list-disc"
          } text-slate-200`}
        >
          {listItems.map((item, i) => (
            <li key={i} className="text-xs leading-relaxed">
              {renderFormattedInlineText(item)}
            </li>
          ))}
        </ListTag>
      );
      listItems = [];
    };

    lines.forEach((line, index) => {
      const lineKey = `line-${index}`;

      if (line.startsWith("```")) {
        if (inCodeBlock) {
          elements.push(
            <div key={lineKey} className="my-2 rounded-lg bg-slate-950 p-3 border border-slate-800 font-mono text-[11px] overflow-x-auto text-amber-300">
              {codeLanguage && (
                <div className="text-[9px] uppercase tracking-wider text-slate-500 font-bold mb-1 border-b border-slate-900 pb-1">
                  {codeLanguage}
                </div>
              )}
              <pre className="whitespace-pre">{codeBlockContent.join("\n")}</pre>
            </div>
          );
          codeBlockContent = [];
          inCodeBlock = false;
          codeLanguage = "";
        } else {
          flushList(`list-before-${lineKey}`);
          inCodeBlock = true;
          codeLanguage = line.replace("```", "").trim();
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        return;
      }

      if (line.startsWith("# ")) {
        flushList(`list-${lineKey}`);
        elements.push(
          <h1 key={lineKey} className="text-base font-bold text-amber-400 mt-3 mb-1">
            {renderFormattedInlineText(line.substring(2))}
          </h1>
        );
        return;
      }

      if (line.startsWith("## ")) {
        flushList(`list-${lineKey}`);
        elements.push(
          <h2 key={lineKey} className="text-sm font-bold text-slate-100 mt-2.5 mb-1 border-b border-slate-800 pb-0.5">
            {renderFormattedInlineText(line.substring(3))}
          </h2>
        );
        return;
      }

      if (line.startsWith("### ")) {
        flushList(`list-${lineKey}`);
        elements.push(
          <h3 key={lineKey} className="text-xs font-bold text-amber-300 mt-2 mb-1">
            {renderFormattedInlineText(line.substring(4))}
          </h3>
        );
        return;
      }

      const unorderedMatch = line.match(/^[\*\-\+]\s+(.*)/);
      if (unorderedMatch) {
        if (isOrderedList && listItems.length > 0) {
          flushList(`flush-${lineKey}`);
        }
        isOrderedList = false;
        listItems.push(unorderedMatch[1]);
        return;
      }

      const orderedMatch = line.match(/^\d+\.\s+(.*)/);
      if (orderedMatch) {
        if (!isOrderedList && listItems.length > 0) {
          flushList(`flush-${lineKey}`);
        }
        isOrderedList = true;
        listItems.push(orderedMatch[1]);
        return;
      }

      if (line.startsWith("> ")) {
        flushList(`list-${lineKey}`);
        elements.push(
          <blockquote key={lineKey} className="my-2 border-l-2 border-amber-500/80 bg-slate-900/60 pl-3 py-1 italic text-slate-300 text-xs rounded-r">
            {renderFormattedInlineText(line.substring(2))}
          </blockquote>
        );
        return;
      }

      if (line.trim() === "") {
        flushList(`list-${lineKey}`);
        elements.push(<div key={lineKey} className="h-1.5" />);
        return;
      }

      flushList(`list-${lineKey}`);
      elements.push(
        <p key={lineKey} className="text-xs leading-relaxed my-1">
          {renderFormattedInlineText(line)}
        </p>
      );
    });

    flushList("list-final");
    return elements;
  };

  const renderFormattedInlineText = (text: string): React.ReactNode[] => {
    const tokens: React.ReactNode[] = [];
    let remaining = text;
    let keyIdx = 0;

    while (remaining.length > 0) {
      const boldMatch = remaining.match(/\*\*(.*?)\*\*/);
      const codeMatch = remaining.match(/`([^`]+)`/);
      const italicMatch = remaining.match(/\*([^*]+)\*/);

      const matches = [
        boldMatch ? { type: "bold", index: boldMatch.index!, match: boldMatch } : null,
        codeMatch ? { type: "code", index: codeMatch.index!, match: codeMatch } : null,
        italicMatch ? { type: "italic", index: italicMatch.index!, match: italicMatch } : null,
      ]
        .filter(Boolean)
        .sort((a, b) => a!.index - b!.index);

      if (matches.length === 0) {
        tokens.push(remaining);
        break;
      }

      const firstMatch = matches[0]!;
      if (firstMatch.index > 0) {
        tokens.push(remaining.substring(0, firstMatch.index));
      }

      if (firstMatch.type === "bold") {
        tokens.push(
          <strong key={`b-${keyIdx++}`} className="font-semibold text-slate-50">
            {firstMatch.match[1]}
          </strong>
        );
      } else if (firstMatch.type === "code") {
        tokens.push(
          <code key={`c-${keyIdx++}`} className="bg-slate-950 text-amber-300 px-1 py-0.5 rounded text-[11px] font-mono border border-slate-800">
            {firstMatch.match[1]}
          </code>
        );
      } else if (firstMatch.type === "italic") {
        tokens.push(
          <em key={`i-${keyIdx++}`} className="italic text-slate-300">
            {firstMatch.match[1]}
          </em>
        );
      }

      remaining = remaining.substring(firstMatch.index + firstMatch.match[0].length);
    }

    return tokens;
  };

  return <div className={`space-y-1 ${className}`}>{parseMarkdownToElements(content)}</div>;
};
