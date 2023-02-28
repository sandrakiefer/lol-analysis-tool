import {
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib";
import React, { ReactNode } from "react";

function Point(props: any) {
  let dot_class = "dot";
  switch (props.event_type) {
    case "Kills":
      dot_class += " kill_dot";
      break;
    case "Deaths":
      dot_class += " death_dot";
      break;
    case "Assists":
      dot_class +=" assist_dot";
      break;
    case "Dragons":
      dot_class += " dragon_dot";
      break;
    case "Heralds":
      dot_class += " herald_dot";
      break;
    case "Barons":
      dot_class += " baron_dot";
      break;
    case "Buildings":
      dot_class += " building_dot";
      break;
  }
  dot_class += " game" + props.game_index
  return (
    <button
      className={props.clicked ? "dot clicked-dot game" + props.game_index : dot_class}
      onClick={props.onClick}
    ></button>
  );
}

interface ITooltipProps {
  xP: number;
  yP: number;
  killer_champ?: string;
  victim_champ?: string;
  assist_champs?: any;
  width: number;
  height: number;
  event_type: string;
  event_time: string;
}

class Tooltip extends React.Component<ITooltipProps> {
  render() {
    var ttxPoint;
    var ttyPoint;

    /**
     * adjust tooltip width/height in case of overflow
     */
    var left = this.props.xP;
    var top = this.props.yP;
    var width = this.props.width;
    var height = this.props.height;
    if (left + 310 > width && top + 170 > height) {
      ttxPoint = left - 325;
      ttyPoint = height - top - 10;
    } else if (left + 310 > width) {
      ttxPoint = left - 325;
      ttyPoint = height - top - 170;
    } else if (top + 170 > height) {
      ttxPoint = left;
      ttyPoint = height - top - 10;
    } else {
      ttxPoint = left;
      ttyPoint = height - top - 170;
    }

    var ttHeaderText = "";
    var ttAssisterText = "";
    var assisters = "";
    
    switch (this.props.event_type) {
      case "Kills":
        ttHeaderText += "You (" + this.props.killer_champ + ") have slain " + this.props.victim_champ;
        if(this.props.assist_champs.length > 0) {
          
          this.props.assist_champs.forEach(function (champ: string) {
            assisters += champ + ' ';
          });
          ttAssisterText += "Assisted by: " + assisters
        }
        else {
          ttAssisterText += "No assists"
        }
        break;
      case "Deaths":
        ttHeaderText += "You (" + this.props.victim_champ + ") were slain by " + this.props.killer_champ;
        if(this.props.assist_champs.length > 0) {
          this.props.assist_champs.forEach(function (champ: string) {
            assisters += champ + ' ';
          });
          ttAssisterText += "Assisted by: " + assisters
        }
        else {
          ttAssisterText += "No assists"
        }
        break;
      case "Assists":
        ttHeaderText += "You assisted " + this.props.killer_champ + " to slay " + this.props.victim_champ;
        this.props.assist_champs.forEach(function (champ: string) {
          assisters += champ + ' ';
        });
        ttAssisterText += "Assisted by: " + assisters
        break;
      case "Dragons":
        ttHeaderText += "Your Team (" + this.props.killer_champ + ") has slain the Dragon";
        if(this.props.assist_champs.length > 0) {
          this.props.assist_champs.forEach(function (champ: string) {
            assisters += champ + ' ';
          });
          ttAssisterText += "Assisted by: " + assisters
        }
        else {
          ttAssisterText += "No assists"
        }
        break;
      case "Heralds":
        ttHeaderText += "Your Team (" + this.props.killer_champ + ") has slain the Herald";
        break;
      case "Barons":
        ttHeaderText += "Your Team (" + this.props.killer_champ + ") has slain the Baron";
        break;
      case "Buildings":
        ttHeaderText += "You (" + this.props.killer_champ + ") destroyed an enemy Building";
        break;
    }

    return (
      <div
        className="ind-tooltip"
        style={{
          position: "fixed",
          left: ttxPoint + "px",
          top: ttyPoint + "px",
        }}
      >
        <div className="tooltip-header">{ttHeaderText}</div>
        <div>
          Timestamp Match: <b>{this.props.event_time}</b> <br /> {ttAssisterText}
        </div>
      </div>
    );
  }
}

interface IIndicatorProps {
  x_coord: number;
  y_coord: number;
  killer_champ?: string;
  victim_champ?: string;
  assist_champs?: any;
  event_type: string;
  event_time: string;
  game_index: number;
  map_height: number;
  map_width: number;
}

interface IIndicatorState {
  showTooltip?: boolean;
}

class Indicator extends React.Component<IIndicatorProps, IIndicatorState> {
  constructor(props: IIndicatorProps) {
    super(props);
    this.state = {
      showTooltip: false,
    };
  }

  handleClick() {
    this.setState({ showTooltip: !this.state.showTooltip });
  }

  render() {
    const WIDTH = this.props.map_width;
    const HEIGHT = this.props.map_height;

    var x_percent = this.props.x_coord / 16000;
    var y_percent = this.props.y_coord / 16000;

    var xPoint = WIDTH * x_percent;
    var yPoint = HEIGHT * y_percent;

    return (
      <div
        className="indicator"
        style={{ left: xPoint + "px", bottom: yPoint + "px" }}
      >
        {this.state.showTooltip && (
          <Tooltip
            xP={xPoint}
            yP={yPoint}
            killer_champ={this.props.killer_champ}
            victim_champ={this.props.victim_champ}
            assist_champs={this.props.assist_champs}
            width={WIDTH}
            height={HEIGHT}
            event_type={this.props.event_type}
            event_time={this.props.event_time}
          />
        )}
        <Point
          onClick={() => this.handleClick()}
          clicked={this.state.showTooltip}
          event_type={this.props.event_type}
          game_index={this.props.game_index}
        />
      </div>
    );
  }
}

class MapComponent extends StreamlitComponentBase {
  public render = (): ReactNode => {
    // Arguments that are passed to the plugin in Python are accessible
    // via `this.props.args`.
    const x_coords = this.props.args["x_coords"];
    const y_coords = this.props.args["y_coords"];
    const killer_champ = this.props.args["killer_champ"];
    const victim_champ = this.props.args["victim_champ"];
    const assist_champs = this.props.args["assist_champs"]
    const event_type = this.props.args["event_type"];
    const events = this.props.args["events"];
    const event_time = this.props.args["event_time"];
    const time_range = this.props.args["time_range"];
    const game_index = this.props.args["game_index"];
    const game_array = this.props.args["game_array"];
    const map_width = this.props.width;
    const map_height = map_width * 0.767;

    const indicatorList = x_coords.map(
      (xCoord: number, index: number) =>
        events.includes(event_type[index]) &&
        game_array[game_index[index]] &&
        event_time[index] >= time_range[0] &&
        event_time[index] <= time_range[1] && (
          <Indicator
            key={index}
            x_coord={xCoord}
            y_coord={y_coords[index]}
            killer_champ={killer_champ[index]}
            victim_champ={victim_champ[index]}
            assist_champs={assist_champs[index]}
            event_type={event_type[index]}
            event_time={event_time[index]}
            game_index={game_index[index]}
            map_height={map_height}
            map_width={map_width}
          />
        )
    );

    return (
      <div id="zoom">
        <img
          src="SR_adjusted_cp.png"
          id="map_img"
          alt="summoners_rift"
          style={{ height: map_height + "px" }}
        ></img>
        <div className="scatter">{indicatorList}</div>
      </div>
    );
  };
}

// "withStreamlitConnection" is a wrapper function. It bootstraps the
// connection between your component and the Streamlit app, and handles
// passing arguments from Python -> Component.

export default withStreamlitConnection(MapComponent);
