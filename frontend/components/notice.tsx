type NoticeProps = {
  children: React.ReactNode;
};

export function Notice({ children }: NoticeProps) {
  return (
    <p
      role="alert"
      className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm"
    >
      {children}
    </p>
  );
}
