declare module 'react-katex' {
    import { FC, ReactNode } from 'react';

    interface KatexProps {
        math: string;
        block?: boolean;
        errorColor?: string;
        renderError?: (error: Error) => ReactNode;
        settings?: object;
    }

    export const InlineMath: FC<KatexProps>;
    export const BlockMath: FC<KatexProps>;
}
