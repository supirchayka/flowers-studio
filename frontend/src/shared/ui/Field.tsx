import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

type BaseFieldProps = {
  label: string;
};

type InputProps = BaseFieldProps & InputHTMLAttributes<HTMLInputElement> & { multiline?: false };
type TextareaProps = BaseFieldProps & TextareaHTMLAttributes<HTMLTextAreaElement> & { multiline: true };

export function Field(props: InputProps | TextareaProps) {
  const { label } = props;

  if (props.multiline) {
    const { multiline: _multiline, ...textareaProps } = props;
    return (
      <label className="field">
        <span>{label}</span>
        <textarea className="field__control field__control--textarea" {...textareaProps} />
      </label>
    );
  }

  const { multiline: _multiline, ...inputProps } = props;
  return (
    <label className="field">
      <span>{label}</span>
      <input className="field__control" {...inputProps} />
    </label>
  );
}

