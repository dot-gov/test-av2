package com.example.zad.report;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.PowerManager;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.view.WindowManager.LayoutParams;
import android.widget.FrameLayout;
import android.widget.TextView;
public class ReportActivity extends Activity {
	PowerManager.WakeLock sScreenWakeLock;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
		getWindow().addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED);
		getWindow().addFlags( LayoutParams.FLAG_KEEP_SCREEN_ON);
	}

	protected void parse_intent(Intent i){
		if (sScreenWakeLock == null) {
			PowerManager pm =
					(PowerManager) getSystemService(Context.POWER_SERVICE);
			sScreenWakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK |
							PowerManager.ACQUIRE_CAUSES_WAKEUP |
							PowerManager.ON_AFTER_RELEASE, "ReportActivity Wakelock");
			sScreenWakeLock.acquire();
		}
		TextView tv=new TextView(this);
		tv.setTextSize(30);
		tv.setGravity(Gravity.CENTER);
		tv.setLayoutParams(new FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.MATCH_PARENT));

		setContentView(R.layout.mainview);
		if (i!=null){
			if ((i != null) && (i.hasExtra("result")))
				tv.setText(i.getStringExtra("result"));
			else
				tv.setText("WELCOME!");
			ViewGroup vg = (ViewGroup) findViewById (R.id.mainView);
			vg.removeAllViews();
			vg.addView(tv);
			vg.invalidate();
		}else{
			//start flashing
			//tv.setBackgroundColor();
		}

	}


	@Override
	protected void onNewIntent(Intent intent) {
		super.onNewIntent(intent);
		parse_intent(intent);
	}

	protected void onStart() {
		super.onStart();
		parse_intent(getIntent());

	}
	protected void onStop() {
		if (sScreenWakeLock != null) {
			sScreenWakeLock.release();
			sScreenWakeLock = null;
		}
		super.onStop();
	}


}