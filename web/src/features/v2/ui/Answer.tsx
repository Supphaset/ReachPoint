import { Fragment } from "react";
import { Link } from "react-router-dom";
import { displayText } from "./trace";
/** Render the supported emphasis and citations as React nodes, never raw HTML. */
export function CopilotAnswer({ text }: { text: string }) {
  return (
    <div className="rp-answer">
      {displayText(text).split(/(\*\*[^*]+\*\*)/g).map((part, index) => (
        part.startsWith("**")
          ? <strong key={index}>
            <CitedText text={part.slice(2, -2)} />
          </strong>
          : <Fragment key={index}>
            <CitedText text={part} />
          </Fragment>
      ))}
    </div>
  );
}

function CitedText({ text }: { text: string }) {
  return <>
    {text.split(/(\[(?:[A-Z]\d+|HH\d+)\])/g).map((part, index) => {
      const citation = /^\[((?:[A-Z]\d+|HH\d+))\]$/.exec(part);
      if (!citation) return <Fragment key={index}>{part}</Fragment>;
      const id = citation[1];
      const page = id.startsWith("HH") ? "case" : "zone";
      return <Link key={index} to={`/v/${page}/${id}`}>{part}</Link>;
    })}
  </>;
}
