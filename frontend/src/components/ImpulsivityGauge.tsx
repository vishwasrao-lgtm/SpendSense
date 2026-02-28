"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface ImpulsivityGaugeProps {
    score: number;
}

export default function ImpulsivityGauge({ score }: ImpulsivityGaugeProps) {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove();

        const width = 280;
        const height = 180;
        const cx = width / 2;
        const cy = height - 20;
        const radius = 110;
        const arcWidth = 18;

        const g = svg
            .attr("viewBox", `0 0 ${width} ${height}`)
            .append("g")
            .attr("transform", `translate(${cx}, ${cy})`);

        const arc = d3.arc<any>().innerRadius(radius - arcWidth).outerRadius(radius);

        // Background segments
        const segments = [
            { start: -Math.PI / 2, end: -Math.PI / 6, color: "#059669" },    // green (0-33)
            { start: -Math.PI / 6, end: Math.PI / 6, color: "#d97706" },     // amber (33-66)
            { start: Math.PI / 6, end: Math.PI / 2, color: "#dc2626" },      // red (66-100)
        ];

        segments.forEach((seg) => {
            g.append("path")
                .datum({ startAngle: seg.start, endAngle: seg.end })
                .attr("d", arc as any)
                .attr("fill", seg.color)
                .attr("opacity", 0.25);
        });

        // Value arc
        const clampedScore = Math.max(0, Math.min(100, score));
        const valueAngle = -Math.PI / 2 + (clampedScore / 100) * Math.PI;
        const valueColor = clampedScore < 33 ? "#10b981" : clampedScore < 66 ? "#f59e0b" : "#ef4444";

        g.append("path")
            .datum({ startAngle: -Math.PI / 2, endAngle: valueAngle })
            .attr("d", arc as any)
            .attr("fill", valueColor);

        // Needle
        const needleLen = radius - arcWidth - 10;
        const needleAngle = valueAngle - Math.PI / 2;
        g.append("line")
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", needleLen * Math.cos(needleAngle))
            .attr("y2", needleLen * Math.sin(needleAngle))
            .attr("stroke", "#e5e7eb")
            .attr("stroke-width", 2.5)
            .attr("stroke-linecap", "round");

        // Center dot
        g.append("circle").attr("r", 5).attr("fill", "#e5e7eb");

        // Score text
        g.append("text")
            .attr("y", -35)
            .attr("text-anchor", "middle")
            .attr("fill", valueColor)
            .attr("font-size", "28px")
            .attr("font-weight", "bold")
            .text(Math.round(clampedScore));

        // Label
        g.append("text")
            .attr("y", -12)
            .attr("text-anchor", "middle")
            .attr("fill", "#9ca3af")
            .attr("font-size", "11px")
            .text("/ 100");

    }, [score]);

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">Impulsivity Score</h3>
            <div className="flex justify-center">
                <svg ref={svgRef} className="w-full max-w-[280px]" />
            </div>
        </div>
    );
}
