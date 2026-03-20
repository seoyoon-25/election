"use client";

import Link from "next/link";
import { ArrowRight, Megaphone, Pin } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState, CardSkeleton } from "@/components/common";
import { formatRelativeDate } from "@/lib/utils";

interface Announcement {
  id: string;
  title: string;
  created_at: string;
  is_pinned?: boolean;
  is_important?: boolean;
}

interface AnnouncementWidgetProps {
  announcements: Announcement[];
  isLoading?: boolean;
  campaignId: string;
}

export function AnnouncementWidget({
  announcements,
  isLoading,
  campaignId,
}: AnnouncementWidgetProps) {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Megaphone className="h-4 w-4 text-primary" />
          공지사항
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <CardSkeleton key={i} className="h-12" />
            ))}
          </div>
        )}

        {!isLoading && announcements.length === 0 && (
          <EmptyState
            title="공지사항이 없습니다"
            icon={<Megaphone className="h-8 w-8 text-muted-foreground" />}
          />
        )}

        {!isLoading && announcements.length > 0 && (
          <>
            <div className="space-y-1 flex-1">
              {announcements.slice(0, 4).map((announcement) => (
                <AnnouncementItem
                  key={announcement.id}
                  announcement={announcement}
                  campaignId={campaignId}
                />
              ))}
            </div>
            <div className="pt-3 mt-auto border-t">
              <Link
                href={`/c/${campaignId}/announcements`}
                className="flex items-center justify-center text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                전체보기
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function AnnouncementItem({
  announcement,
  campaignId,
}: {
  announcement: Announcement;
  campaignId: string;
}) {
  return (
    <Link
      href={`/c/${campaignId}/announcements/${announcement.id}`}
      className="flex items-start gap-2 p-2 rounded-md hover:bg-accent/50 transition-colors"
    >
      {announcement.is_pinned && (
        <Pin className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium line-clamp-1">{announcement.title}</p>
          {announcement.is_important && (
            <Badge variant="destructive" className="text-[10px] h-4 px-1">
              필독
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          {formatRelativeDate(announcement.created_at)}
        </p>
      </div>
    </Link>
  );
}
