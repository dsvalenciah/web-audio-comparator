import React, { Component } from 'react';
import request from 'superagent';
import LinearProgress from '@material-ui/core/LinearProgress';
import CircularProgress from '@material-ui/core/CircularProgress';
import Send from '@material-ui/icons/Send';
import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import FormControl from '@material-ui/core/FormControl';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import Select from '@material-ui/core/Select';



class App extends Component {
	constructor(props) {
		super(props);
		this.state = {
			resultsApi: null,
			bigFile: null,
			littleFile: null,
			loading: false,
			thresholdLine: null,
			comparisionRate: null,
			completed: 0,
			threadsCount: '',
			applyNormalization: ''
		};
	}

	showResults = (base_url) => {
		request
		.get(base_url)
		.set('Accept', 'application/json')
		.then(res => {
		this.setState({
			resultsApi: res.body.result
		});
		})
		.catch(err => {
			console.log(err);
		});
	}

	verifyProgress = (base_url) => {
		request
		.get(base_url)
		.set('Accept', 'application/json')
		.then(res => {
			if (res.body.result.finished_at) {
				this.setState({loading: false});
				this.showResults(base_url);
				clearInterval(this.timer);
			}
			if (res.body.result.error) {
				clearInterval(this.timer);
				// TODO: add error notification
			}
			if (res.body.result.advanced && res.body.result.advanced.length) {
				var percentage = parseInt(res.body.result.advanced[0]);
				this.setState({
					completed: percentage
				});
			}
		})
		.catch(err => {
			console.log(err);
		});
	}

	handleselectedBigFile = event => {
		this.setState({
			bigFile: event.target.files[0],
		  loaded: 0,
		})
	}

	handleselectedLittleFile = event => {
		this.setState({
			littleFile: event.target.files[0],
		  loaded: 0,
		})
	}

	handleTresholdLineChange = event => {
		this.setState({ thresholdLine: event.target.value });
	};

	handleComparisionRateChange = event => {
		this.setState({ comparisionRate: event.target.value });
	};

	handleThreadsCountChange = event => {
		this.setState({ threadsCount: event.target.value });
	};

	handleApplyNormalizationChange = event => {
		this.setState({ applyNormalization: event.target.value });
	}

	handleUpload = () => {
		if (!this.state.bigFile || !this.state.littleFile) { return; }
		var base_url = "https://audio-records-app.herokuapp.com/";
		request
			.post('https://audio-records-app.herokuapp.com/collection')
			.attach('big_file', this.state.bigFile)
			.attach('little_file', this.state.littleFile)
			.field('threshold_line', this.state.thresholdLine || 0.80)
			.field('comparision_rate', this.state.comparisionRate || 0)
			.field('threads_count', this.state.threadsCount || 1)
			.field('apply_normalization', this.state.applyNormalization || false)
			.then(res => {
				if (res.body.id) {
					base_url = base_url.concat(res.body.id);
					this.timer = setInterval(this.verifyProgress, 1500, base_url);
						this.setState({loading: true});
						return;
					} else {
						// TODO: show error notification
					}
			})
	}

	render() {
		return (
			<div className="App" style={{textAlign: "center"}}>
				<Grid container spacing={24}
				  	justify="center"
				  	alignItems="center"
				>
					<Grid item xs={6}>
						<input
							accept="audio/mp3"
							id="contained-big-file"
							type="file"
							style={{display: 'none' }}
							onChange={this.handleselectedBigFile}
						/>
						<label htmlFor="contained-big-file">
							<Button variant="contained" component="span" disabled={this.state.loading}>
								Upload Big File
							</Button>
							{this.state.loading && <CircularProgress size={24} color="secondary"/>}
							<label>
								{this.state.bigFile ? this.state.bigFile.name: "No file selected"}
							</label>
						</label>
					</Grid>
					<Grid item xs={6}>
						<input
							accept="audio/mp3"
							id="contained-little-file"
							type="file"
							style={{display: 'none' }}
							onChange={this.handleselectedLittleFile}
						/>
						<label htmlFor="contained-little-file">
							<Button variant="contained" component="span" disabled={this.state.loading}>
								Upload Little File
							</Button>
							{this.state.loading && <CircularProgress size={24} color="secondary"/>}
							<label>
								{this.state.littleFile ? this.state.littleFile.name: "No file selected"}
							</label>
						</label>
					</Grid>
					<Grid item xs={12}>
						<FormControl style={{minWidth: 300}}>
							<InputLabel htmlFor="component-simple">Threshold line position (0.8 to 0.9)</InputLabel>
							<Input id="component-simple" onChange={this.handleTresholdLineChange} />
						</FormControl>
						<br />
						<FormControl style={{minWidth: 300}}>
							<InputLabel htmlFor="component-simple2">Comparision rate (0.0 to 1.0)</InputLabel>
							<Input id="component-simple2" onChange={this.handleComparisionRateChange} />
						</FormControl>
						<br />
						<FormControl style={{minWidth: 300}}>
							<InputLabel htmlFor="threads-count">Threads count (1 to 4)</InputLabel>
							<Select
								value={this.state.threadsCount}
								onChange={this.handleThreadsCountChange}
								inputProps={{
									name: 'threadsCount',
									id: 'threads-count',
								}}
							>
								<MenuItem value={1}>1</MenuItem>
								<MenuItem value={2}>2</MenuItem>
								<MenuItem value={3}>3</MenuItem>
								<MenuItem value={4}>4</MenuItem>
							</Select>
						</FormControl>
						<br />
						<FormControl style={{minWidth: 300}}>
							<InputLabel htmlFor="apply-normalization">Apply normalization to results</InputLabel>
							<Select
								value={this.state.applyNormalization}
								onChange={this.handleApplyNormalizationChange}
								inputProps={{
									name: 'applyNormalization',
									id: 'apply-normalization',
								}}
							>
								<MenuItem value={true}>Yes</MenuItem>
								<MenuItem value={false}>no</MenuItem>
							</Select>
						</FormControl>
					</Grid>
					<Button
						variant="contained"
						color="primary"
						onClick={this.handleUpload}
						disabled={this.state.loading || !this.state.bigFile || !this.state.littleFile}
						style={{marginRight: "30px"}}
					>
						Start process
        		<Send />
      		</Button>
					{this.state.loading && <CircularProgress size={24} color="secondary"/>}
					<Grid item xs={12}>
						{this.state.loading && <LinearProgress variant="determinate" value={this.state.completed} />}
					</Grid>
				</Grid>
				{this.state.resultsApi && this.state.resultsApi.results &&
					<div>
						<Grid container spacing={24}
							justify="center"
							alignItems="center"
						>
							<TextField
								id="standard-name"
								label="Time start of best precision"
								value={this.state.resultsApi.results.start_second || ""}
								margin="normal"
							/>
							<TextField
								id="standard-name"
								label="Time end of best precision"
								value={this.state.resultsApi.results.end_second || ""}
								margin="normal"
							/>
							<TextField
								id="standard-name"
								label="Process duration"
								value={this.state.resultsApi.results.process_duration || ""}
								margin="normal"
							/>
							<Grid item xs={12}>
								<img alt="" src={this.state.resultsApi.results.distances_overlapping_img  || ""} />
							</Grid>
							<Grid item xs={12}>
								<img alt="" src={this.state.resultsApi.results.best_adjust_overlapping_img  || ""} />
							</Grid>
						</Grid>
					</div>
				}
			</div>
		);
	}
}

export default App;
