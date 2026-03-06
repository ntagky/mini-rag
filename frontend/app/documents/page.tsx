"use client";

import { PdfUpload } from "@/components/custom/pdf-upload";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from "@/components/ui/drawer";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { Item, ItemContent, ItemMedia, ItemTitle } from "@/components/ui/item";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getDocuments, getIngestionStatus, ingestCorpus } from "@/lib/api";
import { DocumentItem, DocumentsResponse, IngestionStatusResponse } from "@/lib/dataclasses";
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu";
import { ListRestart, MoreHorizontal } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function DocumentsPage() {

    const [documents, setDocuments] = useState<DocumentItem[]>([])
    const [unprocessed, setUnprocessed] = useState<string[]>([])
    const [metrics, setMetrics] = useState<{ title: string; value: number }[]>([])
    const [loading, setLoading] = useState(true)
    const [fetching, setFetching] = useState(false)
    const [isIngesting, setIsIngesting] = useState(false)
    const [statusData, setStatusData] = useState<IngestionStatusResponse | null>(null)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)

    useEffect(() => {
        fetchDocuments()
    }, [])

    useEffect(() => {
        const fetchInitialStatus = async () => {
            try {
                const status = await getIngestionStatus()
                setStatusData(status)

                if (status.is_running) {
                    setIsIngesting(true)
                    startPolling()
                }
            } catch (error) {
                console.error("Failed to fetch initial status", error)
            }
        }

        fetchInitialStatus()

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [])

    async function fetchDocuments() {
        try {
            const data: DocumentsResponse = await getDocuments()
            setDocuments(data.ingested_files)
            setUnprocessed(data.unprocessed_filenames)

            const totalPages = data.ingested_files.reduce(
                (sum, doc) => sum + doc.page_count,
                0
            )
            const totalChunks = data.ingested_files.reduce(
                (sum, doc) => sum + doc.chunk_count,
                0
            )

            setMetrics([
                { title: "Ingested Files", value: data.ingested_files.length },
                { title: "Total Pages", value: totalPages },
                { title: "Total Chunks", value: totalChunks },
                { title: "Unprocessed Files", value: data.unprocessed_filenames.length },
            ])
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
            setFetching(false)
        }
    }

    const handleNewFileUploaded = () => {
        setFetching(true)
        fetchDocuments()
    }

    const startPolling = () => {
        if (intervalRef.current) return // prevent double polling

        intervalRef.current = setInterval(async () => {
            try {
                const status = await getIngestionStatus()
                setStatusData(status)

                // Stop polling if ingestion finished
                if (!status.is_running) {
                    setIsIngesting(false)
                    fetchDocuments()

                    if (intervalRef.current) {
                        clearInterval(intervalRef.current)
                        intervalRef.current = null
                    }
                }
            } catch (error) {
                console.error("Polling failed", error)
            }
        }, 10000)
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center space-y-6 h-full w-full mb-8 p-2 text-sm text-muted-foreground">
                <div className="flex flex-col gap-4 [--radius:1rem]">
                    <Item variant="muted">
                        <ItemMedia>
                        <Spinner />
                        </ItemMedia>
                        <ItemContent>
                        <ItemTitle className="line-clamp-1">Loading...</ItemTitle>
                        </ItemContent>
                    </Item>
                </div>
            </div>
        )
    }

    const handleDelete = (id: string) => {
        // TODO - Delete file from corpus and databases
        console.log("Delete file with id:", id)
    }

    const handleIngestion = (reset: boolean) => {
        ingestCorpus(reset).catch(console.error)
        setIsIngesting(true)

        startPolling()
    }

    return (
        <div className="space-y-6 p-2">
            <div className="flex justify-between mt-4 items-center">
                <h2 className="text-xl font-semibold tracking-tight">
                Documents
                </h2>
                <div className="flex items-center gap-2">
                    {fetching === true ?
                        <Badge variant="outline" className="flex gap-2 px-3 py-1 text-orange-500 text-sm">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-500 opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-600" />
                            </span>
                            <span>
                            Synching..
                            </span>
                        </Badge>
                         : <></>}
                    {isIngesting ? (
                        <Badge variant="outline" className="flex gap-2 px-3 py-1 text-green-500 text-sm">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-600" />
                            </span>
                            <span>
                            Ingesting
                            </span>
                        </Badge>
                    ) :
                        <>
                            {unprocessed.length > 0 ?
                                <Dialog>
                                    <DialogTrigger asChild>
                                        <Button variant={unprocessed.length == 0 ? "outline" : "default"}>
                                            Ingest
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent className="sm:max-w-sm">
                                        <DialogHeader>
                                            <DialogTitle>Confirm Ingestion</DialogTitle>
                                            <DialogDescription>
                                            Are you sure you want to scan corpus and ingest unprocessed or updated files?
                                            </DialogDescription>
                                        </DialogHeader>
                                        <Separator/>
                                        <DialogFooter>
                                            <DialogClose asChild>
                                            <Button variant="outline">Cancel</Button>
                                            </DialogClose>
                                            <Button onClick={() => handleIngestion(false)}>Confirm</Button>
                                        </DialogFooter>
                                    </DialogContent>
                                </Dialog>
                            : <></>}
                            <Dialog>
                                <DialogTrigger asChild>
                                    <Button variant={"destructive"} size="icon">
                                        <ListRestart />
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-sm">
                                    <DialogHeader>
                                        <DialogTitle>Reset Ingestion</DialogTitle>
                                        <DialogDescription>
                                        Are you sure you want to reset and rerun ingestion on the corpus?
                                        </DialogDescription>
                                    </DialogHeader>
                                    <Separator/>
                                    <DialogFooter>
                                        <DialogClose asChild>
                                        <Button variant="outline">Cancel</Button>
                                        </DialogClose>
                                        <Button variant={"destructive"} onClick={() => handleIngestion(true)}>Confirm</Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        </>
                    }
                </div>
            </div>
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
                {metrics.map((metric) => (
                    <Card key={metric.title} className="rounded-xl shadow-sm">
                        <CardContent className="flex flex-col items-center justify-center p-1">
                            { metric.title === "Unprocessed Files" ?
                                <Drawer
                                    key={"right"}
                                    direction={"right"}
                                >
                                    <DrawerTrigger asChild>
                                        <div className="text-3xl font-bold cursor-pointer">
                                            {metric.value}
                                        </div>
                                    </DrawerTrigger>
                                    <DrawerContent className="data-[vaul-drawer-direction=bottom]:max-h-[50vh] data-[vaul-drawer-direction=top]:max-h-[50vh]">
                                        <DrawerHeader>
                                        <DrawerTitle>Unprocessed Files</DrawerTitle>
                                        <DrawerDescription>
                                            Freshly added files that have not been ingested yet or files with same name and updated content.
                                        </DrawerDescription>
                                        </DrawerHeader>
                                        <div className="no-scrollbar overflow-y-auto px-4">
                                            {unprocessed.length === 0 ? (
                                                <div className="text-sm">
                                                No unprocessed files found.
                                                </div>
                                            ) : (
                                                <ul className="space-y-2">
                                                {unprocessed.map((file) => (
                                                    <li
                                                    key={file}
                                                    className="flex gap-1 items-center justify-between rounded-lg border px-3 py-2 text-sm"
                                                    >
                                                    <span className="truncate">{file}</span>
                                                    <span className="h-2 w-2 rounded-full bg-red-500" />
                                                    </li>
                                                ))}
                                                </ul>
                                            )}
                                        </div>
                                        <DrawerFooter>
                                        <DrawerClose asChild>
                                            <Button variant="outline">Close</Button>
                                        </DrawerClose>
                                        </DrawerFooter>
                                    </DrawerContent>
                                </Drawer>
                                :
                                <div className="text-3xl font-bold">
                                    {metric.value}
                                </div>
                            }
                            <div className="text-sm text-muted-foreground mt-2">
                            {metric.title}
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <PdfUpload onFileUploaded={handleNewFileUploaded}></PdfUpload>

            {documents.length > 0 &&
                <div>
                    <Table>
                        <TableHeader>
                            <TableRow>
                            <TableHead>Filename</TableHead>
                            <TableHead>Pages</TableHead>
                            <TableHead>Chunks</TableHead>
                            <TableHead>Ingested At</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>

                        <TableBody>
                            {documents.map((file) => (
                            <TableRow key={file.id}>
                                <TableCell className="font-medium">
                                {file.filename}
                                </TableCell>

                                <TableCell>{file.page_count}</TableCell>

                                <TableCell>{file.chunk_count}</TableCell>

                                <TableCell>{(file.ingested_at).replace("T", " ")}</TableCell>

                                <TableCell className="text-right">
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="icon" className="size-8">
                                        <MoreHorizontal />
                                    </Button>
                                    </DropdownMenuTrigger>

                                    <DropdownMenuContent align="end">
                                    <DropdownMenuItem
                                        variant="destructive"
                                        onClick={() => handleDelete(file.id)}
                                    >
                                        Delete
                                    </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                                </TableCell>
                            </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    {statusData?.finished_at !== null ? <p className="text-end text-muted-foreground text-sm">Last synced: {statusData?.finished_at}</p> : <></>}
                </div>
            }
        </div>
    )
}
