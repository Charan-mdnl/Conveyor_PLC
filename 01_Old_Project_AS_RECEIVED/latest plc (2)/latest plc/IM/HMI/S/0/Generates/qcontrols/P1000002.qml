import QtQuick 2.7
import "qrc:/"
IGuiPage
{
	id: q16777218
	objId: 16777218
	x: 0
	y: 0
	width: 800
	height: 480
	IGuiAlarmView
	{
		id: q402653186
		objId: 402653186
		x: 2
		y: 92
		width: 797
		height: 308
		qm_RectangleBorder.width:0
		qm_RectangleBorder.color:"#ff000000"
		qm_FillColor: "#ffcecfce"
		IGuiListCtrl
		{
			id: qu402653186
			objectName: "qu402653186"
			x: 0
			y: 0
			width: 797
			height: 302
			qm_list.qm_linesPerRow: 1
			qm_list.qm_tableRowHeight: 21
			qm_list.qm_tableMarginLeft: 2
			qm_list.qm_tableMarginRight: 1
			qm_list.qm_tableMarginBottom: 1
			qm_list.qm_tableMarginTop: 1
			qm_list.qm_tableBackColor: "#ffcecfce"
			qm_list.qm_tableSelectBackColor: "#ff0000ff"
			qm_list.qm_tableAlternateBackColor: "#ffe7e7ef"
			qm_list.qm_tableTextColor: "#ff000000"
			qm_list.qm_tableSelectTextColor: "#ffffffff"
			qm_list.qm_tableAlternateTextColor: "#ff000000"
			qm_scrollCtrl: qus402653186

			qm_hasHeader: true
			qm_hasBorder: true
			qm_hasHorizontalScrollBar: false
			qm_hasVerticalScrollBar: true
			qm_list.qm_gridLineStyle: 0
			qm_list.qm_gridLineWidth: 0
			qm_list.qm_gridLineColor: "#ff000000"
			qm_columnTypeList: [0, 0, 0, 0, 0]
			totalColumnWidth: 763
			qm_headerItem: qh402653186
			IGuiListHeader
			{
				id: qh402653186
				width: 763
				qm_listItem: qu402653186
				qm_columnWidthList: [28, 76, 107, 98, 454]
				color: "#ff9c9ace"
				qm_tableHeaderTextColor: "#ff000000"
				qm_tableHeaderValueVarTextAlignmentHorizontal: Text.AlignLeft
				qm_tableHeaderValueVarTextAlignmentVertical: Text.AlignVCenter
				qm_tableHeaderMarginLeft: 4
				qm_tableHeaderMarginRight: 2
				qm_tableHeaderMarginBottom: 2
				qm_tableHeaderMarginTop: 2
				qm_noOfColumns: 5
				qm_tableHeaderHeight: 21
				qm_leftImageID: 33
				qm_leftTileTop: 2
				qm_leftTileBottom: 2
				qm_leftTileRight: 2
				qm_leftTileLeft: 2
				qm_middleImageID: 34
				qm_middleTileTop: 2
				qm_middleTileBottom: 2
				qm_middleTileRight: 2
				qm_middleTileLeft: 2
				qm_rightImageID: 35
				qm_rightTileTop: 2
				qm_rightTileBottom: 2
				qm_rightTileRight: 2
				qm_rightTileLeft: 2
				radius: 0
			}
			IGuiListScrollBarCtrl
			{
				id: qus402653186

			}
		}
	}
	IGuiTextField
	{
		id: q268435471
		objId: 268435471
		x: 372
		y: 62
		width: 84
		height: 27
		qm_Transparent : true 
		qm_TextColor: "#ff000000"
		qm_Anchors.bottomMargin: 2
		qm_Anchors.leftMargin: 2
		qm_Anchors.rightMargin: 2
		qm_Anchors.topMargin: 2
	}
}
