import {
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib";
import React, { useRef, useEffect, ReactNode } from "react";
import * as d3 from "d3";

interface IProps {
  data?: any;
  width: number;
  colour: string;
}

const buildScales = (width: number, height: number, x: any) => {
  const margin = { top: 30, right: 30, bottom: 0, left: 100 };
  const xAxis = (g: any) =>
    g
      .attr("transform", `translate(0,${margin.top})`)
      .call(d3.axisTop(x).ticks(width / 80, "s"))
      .call((g: any) =>
        (g.selection ? g.selection() : g).select(".domain").remove()
      );

  const yAxis = (g: any) =>
    g.attr("transform", `translate(${margin.left + 0.5}, 0)`).call((g: any) =>
      g
        .append("line")
        .attr("stroke", "currentColor")
        .attr("y1", margin.top)
        .attr("y2", height - margin.bottom)
    );
  return [xAxis, yAxis];
};

export const MyD3Component = (props: IProps) => {
  const d3Container = useRef(null);
  useEffect(() => {
    if (props.data && d3Container.current) {
      const root = d3
        .hierarchy(props.data)
        .sum((d) => d.value)
        .sort((a, b) => (b as any).value - (a as any).value)
        .eachAfter(
          (d) =>
            ((d as any).index = d.parent
              ? ((d.parent as any).index = (d.parent as any).index + 1 || 0)
              : 0)
        );

      const margin = { top: 30, right: 30, bottom: 0, left: 100 };
      const barStep = 27;
      const barPadding = 3 / barStep;
      const duration = 750;
      const color = d3.scaleOrdinal([true, false], [props.colour, "#aaa"]);
      const width = props.width;
      const height = (function () {
        let max = 1;
        root.each(
          (d) => d.children && (max = Math.max(max, d.children.length))
        );
        return max * barStep + margin.top + margin.bottom;
      })();

      const stagger = function () {
        let value = 0;
        return (d: any, i: any) => {
          const t = `translate(${x(value) - x(0)},${barStep * i})`;
          value += d.value;
          return t;
        };
      };

      const stack = function (i: any) {
        let value = 0;
        return (d: any) => {
          const t = `translate(${x(value) - x(0)},${barStep * i})`;
          value += d.value;
          return t;
        };
      };

      const bar = function (svg: any, down: any, d: any, selector: any) {
        const g = svg
          .insert("g", selector)
          .attr("class", "enter")
          .attr(
            "transform",
            `translate(0,${margin.top + barStep * barPadding})`
          )
          .attr("text-anchor", "end")
          .style("font", "10px sans-serif")
          .style("fill", "white");

        const bar = g
          .selectAll("g")
          .data(d.children)
          .join("g")
          .attr("cursor", (d: any) => (!d.children ? null : "pointer"))
          .on("click", (event: any, d: any) => down(svg, d));

        bar
          .append("text")
          .attr("x", margin.left - 6)
          .attr("y", (barStep * (1 - barPadding)) / 2)
          .attr("dy", ".35em")
          .text((d: any) => d.data.name);

        bar
          .append("rect")
          .attr("x", x(0))
          .attr("width", (d: any) => x(d.value) - x(0))
          .attr("height", barStep * (1 - barPadding));

        return g;
      };

      const down = function (svg: any, d: any) {
        if (!d.children || d3.active(svg.node())) return;

        // Rebind the current node to the background.
        svg.select(".background").datum(d);

        // Define two sequenced transitions.
        const transition1 = svg.transition().duration(duration);
        const transition2 = transition1.transition();

        // Mark any currently-displayed bars as exiting.
        const exit = svg.selectAll(".enter").attr("class", "exit");

        // Entering nodes immediately obscure the clicked-on bar, so hide it.
        exit
          .selectAll("rect")
          .attr("fill-opacity", (p: any) => (p === d ? 0 : null));

        // Transition exiting bars to fade out.
        exit.transition(transition1).attr("fill-opacity", 0).remove();

        // Enter the new bars for the clicked-on data.
        // Per above, entering bars are immediately visible.
        const enter = bar(svg, down, d, ".y-axis").attr("fill-opacity", 0);

        // Have the text fade-in, even though the bars are visible.
        enter.transition(transition1).attr("fill-opacity", 1);

        // Transition entering bars to their new y-position.
        enter
          .selectAll("g")
          .attr("transform", stack(d.index))
          .transition(transition1)
          .attr("transform", stagger());

        // Update the x-scale domain.
        x.domain([0, d3.max(d.children, (d: any) => d.value)] as any);

        // Update the x-axis.
        svg.selectAll(".x-axis").transition(transition2).call(xAxis);

        // Transition entering bars to the new x-scale.
        enter
          .selectAll("g")
          .transition(transition2)
          .attr("transform", (d: any, i: any) => `translate(0,${barStep * i})`);

        // Color the bars as parents; they will fade to children if appropriate.
        enter
          .selectAll("rect")
          .attr("fill", color(true))
          .attr("fill-opacity", 1)
          .transition(transition2)
          .attr("fill", (d: any) => color(!!d.children))
          .attr("width", (d: any) => x(d.value) - x(0));
      };

      const up = function (svg: any, d: any) {
        if (!d.parent || !svg.selectAll(".exit").empty()) return;

        // Rebind the current node to the background.
        svg.select(".background").datum(d.parent);

        // Define two sequenced transitions.
        const transition1 = svg.transition().duration(duration);
        const transition2 = transition1.transition();

        // Mark any currently-displayed bars as exiting.
        const exit = svg.selectAll(".enter").attr("class", "exit");

        // Update the x-scale domain.
        x.domain([0, d3.max(d.parent.children, (d: any) => d.value)] as any);

        // Update the x-axis.
        svg.selectAll(".x-axis").transition(transition1).call(xAxis);

        // Transition exiting bars to the new x-scale.
        exit
          .selectAll("g")
          .transition(transition1)
          .attr("transform", stagger());

        // Transition exiting bars to the parent’s position.
        exit
          .selectAll("g")
          .transition(transition2)
          .attr("transform", stack(d.index));

        // Transition exiting rects to the new scale and fade to parent color.
        exit
          .selectAll("rect")
          .transition(transition1)
          .attr("width", (d: any) => x(d.value) - x(0))
          .attr("fill", color(true));

        // Transition exiting text to fade out.
        // Remove exiting nodes.
        exit.transition(transition2).attr("fill-opacity", 0).remove();

        // Enter the new bars for the clicked-on data's parent.
        const enter = bar(svg, down, d.parent, ".exit").attr("fill-opacity", 0);

        enter
          .selectAll("g")
          .attr("transform", (d: any, i: any) => `translate(0,${barStep * i})`);

        // Transition entering bars to fade in over the full duration.
        enter.transition(transition2).attr("fill-opacity", 1);

        // Color the bars as appropriate.
        // Exiting nodes will obscure the parent bar, so hide it.
        // Transition entering rects to the new x-scale.
        // When the entering parent rect is done, make it visible!
        enter
          .selectAll("rect")
          .attr("fill", (d: any) => color(!!d.children))
          .attr("fill-opacity", (p: any) => (p === d ? 0 : null))
          .transition(transition2)
          .attr("width", (d: any) => x(d.value) - x(0))
          .on("end", function (this: any, p: any) {
            d3.select(this).attr("fill-opacity", 1);
          });
      };

      const x = d3.scaleLinear().range([margin.left, width - margin.right]);
      x.domain([0, root.value] as any);

      const svg = d3
        .select(d3Container.current)
        .attr("width", width)
        .attr("height", height);
      const [xAxis, yAxis] = buildScales(width, height, x);

      svg
        .select(".background")
        .attr("fill", "none")
        .attr("pointer-events", "all")
        .attr("width", width)
        .attr("height", height)
        .attr("cursor", "pointer")
        .on("click", (event, d) => up(svg, d));

      svg.select(".x-axis").call(xAxis);
      svg.select(".y-axis").call(yAxis);
      down(svg, root);
    }
  }, [props.data, props.width, props.colour]);

  return (
    <svg ref={d3Container} style={{ height: 350 + "px" }}>
      <rect className="background" />
      <g className="x-axis" />
      <g className="y-axis" />
    </svg>
  );
};

class ChartComponent extends StreamlitComponentBase {
  public render = (): ReactNode => {
    return <MyD3Component data={this.props.args["jsonData"]} width = {900} colour={this.props.args["chartColour"]}/>;
  };
}

// "withStreamlitConnection" is a wrapper function. It bootstraps the
// connection between your component and the Streamlit app, and handles
// passing arguments from Python -> Component.

export default withStreamlitConnection(ChartComponent);
