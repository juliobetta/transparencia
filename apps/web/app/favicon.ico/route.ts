import fs from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export async function GET() {
  const icoPath = path.join(process.cwd(), "public", "favicon.ico");
  const pngPath = path.join(process.cwd(), "public", "favicon-32.png");

  const filePath = fs.existsSync(icoPath) ? icoPath : pngPath;

  if (fs.existsSync(filePath)) {
    const fileBuffer = fs.readFileSync(filePath);
    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": "image/x-icon",
        "Cache-Control": "public, max-age=86400, immutable",
      },
    });
  }

  return new NextResponse(null, { status: 404 });
}
