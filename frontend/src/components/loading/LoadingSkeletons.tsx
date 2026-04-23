import { Card, CardContent, Grid, Skeleton, Stack } from "@mui/material";

export function PageIntroSkeleton() {
  return (
    <Stack spacing={1}>
      <Skeleton variant="text" width={140} height={20} />
      <Skeleton variant="text" width="56%" height={52} />
      <Skeleton variant="text" width="82%" height={28} />
      <Skeleton variant="text" width="70%" height={28} />
    </Stack>
  );
}

export function FilterCardSkeleton(props: { fields?: number }) {
  return (
    <Card>
      <CardContent>
        <Grid container spacing={2}>
          {Array.from({ length: props.fields ?? 4 }).map((_, index) => (
            <Grid key={`filter-skeleton-${index}`} size={{ xs: 12, md: 3 }}>
              <Skeleton variant="rounded" height={56} />
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}

export function MetricGridSkeleton(props: { cards?: number }) {
  return (
    <Grid container spacing={2}>
      {Array.from({ length: props.cards ?? 3 }).map((_, index) => (
        <Grid key={`metric-skeleton-${index}`} size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Skeleton variant="text" width={120} height={20} />
                <Skeleton variant="text" width={90} height={40} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

export function ContentCardSkeleton(props: { rows?: number; height?: number }) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.25}>
          <Skeleton variant="text" width="45%" height={32} />
          {Array.from({ length: props.rows ?? 4 }).map((_, index) => (
            <Skeleton
              key={`content-skeleton-${index}`}
              variant="text"
              width={index % 2 === 0 ? "100%" : "88%"}
              height={24}
            />
          ))}
          <Skeleton variant="rounded" height={props.height ?? 120} />
        </Stack>
      </CardContent>
    </Card>
  );
}

export function CardGridSkeleton(props: { cards?: number }) {
  return (
    <Grid container spacing={2}>
      {Array.from({ length: props.cards ?? 3 }).map((_, index) => (
        <Grid key={`card-grid-skeleton-${index}`} size={{ xs: 12, md: 6, xl: 4 }}>
          <ContentCardSkeleton rows={4} height={76} />
        </Grid>
      ))}
    </Grid>
  );
}
