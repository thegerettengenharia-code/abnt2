import { auth } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import { NextRequest, NextResponse } from "next/server"

export async function GET() {
  const session = await auth()
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const works = await prisma.work.findMany({
    where: { userId: session.user.id },
    include: { template: true, _count: { select: { versions: true } } },
    orderBy: { updatedAt: "desc" },
  })

  return NextResponse.json(works)
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const { title, templateId, metadata } = await req.json()

  // Get template content if templateId provided
  let content: any = { type: "doc", content: [] }
  if (templateId) {
    const template = await prisma.template.findUnique({ where: { id: templateId } })
    if (template) content = template.content
  }

  const work = await prisma.work.create({
    data: {
      title,
      templateId,
      userId: session.user.id,
      content,
      metadata,
    },
  })

  return NextResponse.json(work)
}