import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { NextRequest, NextResponse } from "next/server"

export async function GET() {
  const session = await auth()
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const templates = await prisma.template.findMany({
    where: { isOfficial: true },
    orderBy: { category: "asc" },
  })

  return NextResponse.json(templates)
}