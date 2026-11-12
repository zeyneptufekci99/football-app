import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

type CardContainerProps = {
  children: React.ReactNode;
  header?: string;
  contentClassName?: string;
};

export function CardContainer({
  children,
  header,
  contentClassName,
}: CardContainerProps) {
  return (
    <Card className="mt-6 bg-white">
      {header && (
        <CardHeader>
          <CardTitle className="text-lg">Son 5 maç</CardTitle>
        </CardHeader>
      )}
      <CardContent className={contentClassName}>{children}</CardContent>
    </Card>
  );
}
