import { h, Fragment } from "preact";
import { CLIENT_SCRIPTS } from "../scripts";

interface LayoutProps {
    title: string;
    children: any;
}

export const Layout = ({ title, children }: LayoutProps) => (
    <html lang="en">
        <head>
            <meta charSet="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{title}</title>
            <link rel="stylesheet" href="/style.css" />
            {/* PrismJS Theme (GitHub Light style) */}
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" />
        </head>
        <body>
            <header>
                <div class="container nav">
                    <a href="/" class="logo"><span>nlpm</span> Registry</a>
                </div>
            </header>
            <main class="container">
                {children}
            </main>
            
            {/* Scripts */}
            <script dangerouslySetInnerHTML={{ __html: CLIENT_SCRIPTS }} />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
        </body>
    </html>
);