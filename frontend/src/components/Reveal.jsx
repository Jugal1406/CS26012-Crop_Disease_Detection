import { useRef } from "react";
import { useInView } from "../hooks/useInView";

/**
 * Fades (and slightly lifts/un-blurs) its children the first time they scroll into view.
 * `delay` is in milliseconds, handy for staggering a group of items.
 */
export function Reveal({ as: Tag = "div", delay = 0, className = "", style, children, ...rest }) {
  const ref = useRef(null);
  const inView = useInView(ref);
  return (
    <Tag
      ref={ref}
      className={`lp-reveal ${inView ? "is-in" : ""} ${className}`}
      style={{ ...style, "--d": `${delay}ms` }}
      {...rest}
    >
      {children}
    </Tag>
  );
}

/**
 * Splits a heading into words that rise into place one after another.
 * Screen readers get the plain sentence via aria-label.
 */
export function SplitWords({ text, as: Tag = "h2", className = "", start = 0, step = 70, play = true, id }) {
  const words = text.split(" ");
  return (
    <Tag id={id} className={`lp-split ${play ? "is-in" : ""} ${className}`} aria-label={text}>
      {words.map((w, i) => (
        <span key={i} className="lp-split__word" aria-hidden="true" style={{ "--d": `${start + i * step}ms` }}>
          {w}
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </Tag>
  );
}

/** SplitWords that waits until it is scrolled into view. */
export function RevealHeading({ text, as = "h2", className = "", id }) {
  const ref = useRef(null);
  const inView = useInView(ref);
  return (
    <div ref={ref}>
      <SplitWords id={id} text={text} as={as} className={className} play={inView} />
    </div>
  );
}
